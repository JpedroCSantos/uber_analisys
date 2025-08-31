import os
import sys
import psycopg2
import pandas as pd

from io import StringIO
from loguru import logger
from typing import Dict, Optional
from contextlib import contextmanager

class db_class():
    def get_db_params(self, config: Optional[str] = None) -> Dict:
        return {
            "host": config["host"],
            "port": config["port"],
            "dbname": config["dbname"],
            "user": config["user"],
            "password": config["password"],

            "connect_timeout": config.get("connect_timeout", 10),
            "sslmode": config.get("sslmode", "require"),
            "application_name": config.get("application_name", "etl_uber"),

            "keepalives": config.get("keepalives", 1),
            "keepalives_idle": config.get("keepalives_idle", 30),
            "keepalives_interval": config.get("keepalives_interval", 10),
            "keepalives_count": config.get("keepalives_count", 5),
        }
    
    def connect_db(self) -> str:
        if self._is_connected:
            logger.info("Conexão já está ativa")
            return
        
        attempts = 0
        last_error = None
        while attempts < 3:
            try:
                logger.info("Conectando ao banco de dados PostgreSQL...")
                self._connection = psycopg2.connect(**self.params)
                self._connection.autocommit = False 
                self._is_connected = True

                with self._connection.cursor() as cur:
                    cur.execute("SELECT version();")
                    db_version = cur.fetchone()
                    logger.success(f"Conectado com sucesso! Versão: {db_version[0]}")
                logger.success("Conexão estabelecida com sucesso")
                return
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as error:
                last_error = error
                attempts += 1
                wait_s = 120
                logger.warning(f"Falha de conexão (tentativa {attempts}/3): {error}. Retentando em {wait_s}s...")
                try:
                    import time
                    time.sleep(wait_s)
                except Exception:
                    pass
            except (Exception, psycopg2.DatabaseError) as error:
                last_error = error
                logger.error(f"Erro ao conectar ou operar no PostgreSQL: {error}")
                break
        raise last_error

    def disconnect_db(self):
        """Fecha a conexão com o banco"""
        if self._connection and self._is_connected:
            self._connection.close()
            self._is_connected = False
            logger.info("Conexão com PostgreSQL fechada")

    def is_connected(self) -> bool:
        """Verifica se a conexão está ativa"""
        if not self._connection or not self._is_connected:
            return False
        
        try:
            with self._connection.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            self._is_connected = False
            return False
    
    def ensure_connection(self):
        """Garante que a conexão está ativa, reconecta se necessário"""
        if not self.is_connected():
            logger.warning("Conexão perdida, reconectando...")
            self.disconnect_db() 
            self.connect_db()
    
    @contextmanager
    def get_cursor(self, commit=True):
        """Context manager para operações com cursor"""
        self.ensure_connection()
        cursor = self._connection.cursor()
        try:
            yield cursor
            if commit:
                self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Erro na operação do banco: {e}")
            # raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params=None, fetch=False):
        """Executa uma query e opcionalmente retorna resultados"""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
    
    def load_dataframe_to_table(self, df: pd.DataFrame, table_name: str, schema: str = "public", method: str = "execute_values"):
        """
        Carrega DataFrame para tabela PostgreSQL.
        
        Args:
            df: DataFrame a ser carregado
            table_name: Nome da tabela de destino
            schema: Schema da tabela (default: public)
            method: Método de carga ("execute_values" ou "copy_stdin")
        """
        self.ensure_connection()
        
        if schema == "silver" and table_name == "fact_trips":
            self._handle_partitioning(df)
        
        if method == "copy_stdin":
            logger.info("Usando método COPY FROM STDIN (experimental)")
            try:
                self._load_with_copy_from_stdin(df, table_name, schema)
            except Exception as e:
                logger.warning(f"COPY falhou, fallback para execute_values: {e}")
                self._load_with_execute_values(df, table_name, schema)
        else:
            self._load_with_execute_values(df, table_name, schema)

    def _load_with_execute_values(self, df: pd.DataFrame, table_name: str, schema: str = "public", size: int = 20000):
        """
        Carrega dados usando psycopg2.extras.execute_values
        Método confiável e performático para inserção em lote
        """
        from psycopg2.extras import execute_values
        import time
        
        start_time = time.time()
        
        existing_columns = self._get_table_columns(table_name, schema)
        if existing_columns:
            safe_columns = [c for c in df.columns if c in set(existing_columns)]
            if not safe_columns:
                logger.error(f"Nenhuma coluna do DataFrame existe em {schema}.{table_name}. Colunas tabela={existing_columns}, df={list(df.columns)}")
                # raise ValueError("DataFrame não possui colunas compatíveis com a tabela de destino")
            df_filtered = df[safe_columns]
        else:
            df_filtered = df
        
        logger.info(f"Iniciando carga via execute_values: {len(df_filtered)} registros")
        
        placeholders = ', '.join(['%s'] * len(df_filtered.columns))
        insert_sql = f"INSERT INTO {schema}.{table_name} ({', '.join(df_filtered.columns)}) VALUES %s"
        
        data_tuples = [tuple(row) for row in df_filtered.values]
        
        with self.get_cursor(commit=False) as cur:
            batch_size = 10000
            total_inserted = 0
            
            for i in range(0, len(data_tuples), batch_size):
                batch = data_tuples[i:i + batch_size]
                
                execute_values(
                    cur,
                    insert_sql,
                    batch,
                    template=f"({placeholders})",
                    page_size=batch_size
                )
                self._connection.commit()
                
                total_inserted += len(batch)
                
                if total_inserted % size == 0 or total_inserted == len(data_tuples):
                    logger.info(f"Inseridos {total_inserted}/{len(data_tuples)} registros...")
        
        elapsed_time = time.time() - start_time
        logger.success(f"✅ Carga concluída via execute_values: {total_inserted} registros em {elapsed_time:.2f}s")

    def _load_with_copy_from_stdin(self, df: pd.DataFrame, table_name: str, schema: str = "public"):
        """
        Carrega dados usando COPY FROM STDIN
        Método mais rápido, mas com limitações de ambiente/permissões
        NOTA: Mantido para uso futuro quando bugs forem resolvidos
        """
        
        logger.info(f"Tentativa de carga via COPY FROM STDIN: {len(df)} registros")
        
        with StringIO() as memoryFile:
            output = memoryFile
            df.to_csv(output, sep='\t', header=False, index=False, na_rep='\\N')
            output.seek(0)
            
            try:
                self._connection.commit()
                
                old_autocommit = self._connection.autocommit
                self._connection.autocommit = True
                
                cur = self._connection.cursor()
                cur.execute(f"SET search_path TO {schema}, public;")
                
                cur.copy_from(
                    output,
                    f"{schema}.{table_name}",
                    columns=df.columns.tolist(),
                    sep='\t',
                    null='\\N'
                )
                
                cur.close()
                self._connection.autocommit = old_autocommit
                
                logger.success(f"✅ COPY FROM STDIN funcionou: {len(df)} registros")
                
            except Exception as e:
                try:
                    self._connection.autocommit = old_autocommit
                except:
                    pass
                logger.warning(f"COPY FROM STDIN falhou: {e}")
                # raise

    def _get_table_columns(self, table_name: str, schema: str = "public"):
        """Obtém lista de colunas da tabela para validação"""
        try:
            with self.get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema, table_name))
                return [row[0] for row in cur.fetchall()]
        except Exception as e:
            logger.warning(f"Não foi possível obter colunas da tabela {schema}.{table_name}: {e}")
            return None

    def _handle_partitioning(self, df: pd.DataFrame):
        """Gerencia criação automática de partições para fact_trips"""
        try:
            pickup_series = pd.to_datetime(df['pickup_at'], errors='coerce')
            min_date = pickup_series.min()
            max_date = pickup_series.max()

            min_period = min_date.to_period('M')
            max_period = max_date.to_period('M')
            
            logger.info(f"Dados abrangem de {min_period} até {max_period}")
            
            current_period = min_period
            while current_period <= max_period:
                initial_date = pd.Timestamp(current_period.start_time)
                final_date = pd.Timestamp((current_period + 1).start_time)
                
                partition_name = self.get_date_partition(initial_date)
                
                if not self.verify_exists_partition("fact_trips", partition_name, "silver"):
                    logger.info(f"Criando partição para {current_period}: {partition_name}")
                    try:
                        self.create_partition("fact_trips", partition_name, initial_date, final_date, schema="silver")
                    except Exception as e:
                        logger.warning(f"Falha ao criar partição {partition_name}: {e}")
                else:
                    logger.debug(f"Partição {partition_name} já existe")
                
                current_period += 1
                
        except Exception as e:
            logger.warning(f"Erro no particionamento automático: {e}")
        
    def get_date_partition(self, date) -> str:
        """Retorna o nome da partição para uma data específica"""
        if hasattr(date, 'strftime'):
            return date.strftime("%Y_%m")
        else:
            from datetime import datetime
            dt = datetime.fromisoformat(str(date))
            return dt.strftime("%Y_%m")
    
    def verify_exists_partition(self, table_name: str, partition_name: str, schema: str = "public") -> bool:
        """Verifica se a partição existe (PostgreSQL moderno)"""
        with self.get_cursor(commit=False) as cur:
            cur.execute(
                "SELECT to_regclass(%s)",
                (f"{schema}.{table_name}_{partition_name}",)
            )
            return cur.fetchone()[0] is not None

    def create_partition(self, table_name: str, partition_name: str, initial_date, final_date, schema: str = "silver") -> bool:
        """Cria uma partição (qualificando com schema)"""
        with self.get_cursor() as cur:
            cur.execute(
                f"CREATE TABLE {schema}.{table_name}_{partition_name} PARTITION OF {schema}.{table_name} "
                f"FOR VALUES FROM (%s) TO (%s);",
                (str(initial_date), str(final_date))
            )
            cur.execute(
                f"ALTER TABLE {schema}.{table_name}_{partition_name} OWNER TO {self.params['user']};"
            )
            logger.success(f"Partição {schema}.{table_name}_{partition_name} criada com sucesso")
            return True

    def refresh_materialized_view(self, view_name: str, schema: str = "public"):
        """Atualiza uma view materializada com validação de existência e logs úteis"""
        logger.info(f"Atualizando view materializada {schema}.{view_name}")
        is_matview = self.fetch_value(
            """
            SELECT 1
            FROM pg_matviews
            WHERE schemaname = %s AND matviewname = %s
            LIMIT 1
            """,
            (schema, view_name)
        )
        if not is_matview:
            is_view = self.fetch_value(
                """
                SELECT 1
                FROM information_schema.views
                WHERE table_schema = %s AND table_name = %s
                LIMIT 1
                """,
                (schema, view_name)
            )
            if is_view:
                logger.error(f"{schema}.{view_name} é uma VIEW normal, não materializada. Use CREATE MATERIALIZED VIEW para suportar REFRESH.")
            else:
                candidates = self.fetch_all(
                    """
                    SELECT schemaname, matviewname
                    FROM pg_matviews
                    WHERE matviewname ILIKE %s
                    ORDER BY schemaname, matviewname
                    LIMIT 10
                    """,
                    (f"%{view_name}%",)
                )
                logger.error(f"Materialized view {schema}.{view_name} não encontrada. Candidatas: {candidates}")
            return False

        with self.get_cursor(commit=True) as cur:
            cur.execute(f"REFRESH MATERIALIZED VIEW {schema}.{view_name};")
            logger.success(f"View materializada {schema}.{view_name} atualizada com sucesso")
            return True

    def truncate_table(self, table_name: str, schema: str = "public"):
        """Trunca uma tabela"""
        logger.info(f"Truncando tabela {schema}.{table_name}")
        with self.get_cursor(commit=True) as cur:
            cur.execute(f"TRUNCATE TABLE {schema}.{table_name} CASCADE;")
            logger.success(f"Tabela {schema}.{table_name} truncada com sucesso")
            return True

    def fetch_one(self, query: str, params=None):
        """Retorna uma linha (ou None)"""
        with self.get_cursor(commit=False) as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetch_all(self, query: str, params=None):
        """Retorna todas as linhas (lista de tuplas)"""
        with self.get_cursor(commit=False) as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def fetch_value(self, query: str, params=None):
        """Retorna um único valor (primeira coluna da primeira linha)"""
        row = self.fetch_one(query, params)
        return row[0] if row else None

    def execute_non_query(self, query: str, params=None):
        """INSERT/UPDATE/DELETE/DDL (commit automático)"""
        with self.get_cursor(commit=True) as cur:
            cur.execute(query, params)

    def executemany(self, query: str, seq_of_params, batch_size: int = 1000):
        """
        Executa em lotes (INSERT/UPDATE/DELETE). Útil para pequenas cargas.
        Para cargas grandes prefira execute_values.
        """
        with self.get_cursor(commit=True) as cur:
            from itertools import islice
            iterator = iter(seq_of_params)
            while True:
                batch = list(islice(iterator, batch_size))
                if not batch:
                    break
                cur.executemany(query, batch)
    
    def upsert_dim_zone(self, rows):
        """
        rows: iterable de tuplas (zone_id, borough, zone_name)
        """
        sql = """
            INSERT INTO silver.dim_zone (zone_id, borough, zone_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (zone_id) DO UPDATE
            SET borough = EXCLUDED.borough,
                zone_name = EXCLUDED.zone_name
        """
        self.executemany(sql, rows, batch_size=1000)

    def setup_database_schema(self) -> bool:
        """
        Executa script SQL para criar schemas e tabelas necessárias.
        Integração com create_tables.sql
        """
        try:
            sql_file_path = os.path.join("app", "sql", "create_tables.sql")
            if not os.path.exists(sql_file_path):
                logger.warning(f"Arquivo SQL não encontrado: {sql_file_path}")
                return False
                
            return self.execute_sql_file(sql_file_path)
        except Exception as e:
            logger.error(f"Erro ao configurar esquema do banco: {e}")
            return False

    def execute_sql_file(self, file_path: str) -> bool:
        """Executa comandos SQL de um arquivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_commands = file.read()
            
            commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
            
            with self.get_cursor(commit=True) as cur:
                for command in commands:
                    if command:
                        cur.execute(command)
                        
            logger.success(f"Script SQL executado com sucesso: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao executar script SQL {file_path}: {e}")
            return False
    
    def __init__(self, config: Optional[str] = None):
        self.params = self.get_db_params(config)
        self._connection = None
        self._is_connected = False

    def __enter__(self):
        """Suporte a context manager"""
        self.connect_db()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automático no context manager"""
        self.disconnect_db()

    def __del__(self):
        """Cleanup no destructor"""
        if hasattr(self, '_connection'):
            self.disconnect_db()