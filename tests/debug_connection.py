"""
Script de diagnóstico para problemas de conexão e permissões PostgreSQL
"""
import psycopg2
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Parâmetros de conexão


def debug_connection(conn: Optional[psycopg2.connect] = None):
    print("=== DIAGNÓSTICO DE CONEXÃO PostgreSQL ===")
    if not conn:
        params = {
            "host": os.getenv("PG_HOST", "localhost"),
            "port": int(os.getenv("PG_PORT", "5432")),
            "dbname": os.getenv("PG_DATABASE", "trips_analysis"),
            "user": os.getenv("PG_USER", "etl_process"),
            "password": os.getenv("PG_PASSWORD", "postgres")
        }
        conn = psycopg2.connect(**params)
        # Conecta ao banco
        print("1. Tentando conectar...")
        print(f"Parâmetros de conexão: {params}")
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        print("✅ Conexão estabelecida com sucesso!")

    try:
        # Informações básicas
        print("\n2. Informações da conexão:")
        cur.execute("SELECT current_database(), current_user, session_user;")
        db_info = cur.fetchone()
        print(f"   Banco atual: {db_info[0]}")
        print(f"   Usuário atual: {db_info[1]}")
        print(f"   Usuário da sessão: {db_info[2]}")
        
        # Verifica versão do PostgreSQL
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"   Versão PostgreSQL: {version}")
        
        # Lista schemas disponíveis
        print("\n3. Schemas disponíveis:")
        cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
        schemas = [row[0] for row in cur.fetchall()]
        print(f"   Schemas: {schemas}")
        
        # Verifica schema bronze
        print("\n4. Verificando schema bronze:")
        bronze_exists = 'bronze' in schemas
        print(f"   Schema bronze existe: {bronze_exists}")
        
        if bronze_exists:
            # Lista tabelas no bronze
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'bronze'
                ORDER BY table_name;
            """)
            bronze_tables = [row[0] for row in cur.fetchall()]
            print(f"   Tabelas no bronze: {bronze_tables}")
            
            # Verifica se raw_trips_landing existe
            if 'raw_trips_landing' in bronze_tables:
                print("   ✅ Tabela raw_trips_landing encontrada!")
                
                # Testa acesso à tabela
                print("\n5. Testando acesso à tabela:")
                try:
                    cur.execute("SELECT COUNT(*) FROM bronze.raw_trips_landing;")
                    count = cur.fetchone()[0]
                    print(f"   ✅ Acesso bem-sucedido! Registros: {count}")
                except psycopg2.Error as e:
                    print(f"   ❌ Erro ao acessar tabela: {e}")
                    print(f"   Código do erro: {e.pgcode}")
                    print(f"   Detalhe: {e.pgerror}")
                
                # Verifica permissões específicas
                print("\n6. Verificando permissões:")
                cur.execute("""
                    SELECT 
                        grantee,
                        privilege_type
                    FROM information_schema.table_privileges 
                    WHERE table_schema = 'bronze' 
                    AND table_name = 'raw_trips_landing'
                    AND grantee = current_user;
                """)
                user_permissions = cur.fetchall()
                print(f"   Permissões do usuário atual: {user_permissions}")
                
                # Verifica todas as permissões da tabela
                cur.execute("""
                    SELECT 
                        grantee,
                        privilege_type
                    FROM information_schema.table_privileges 
                    WHERE table_schema = 'bronze' 
                    AND table_name = 'raw_trips_landing';
                """)
                all_permissions = cur.fetchall()
                print(f"   Todas as permissões da tabela: {all_permissions}")
                
                # Verifica roles do usuário
                cur.execute("""
                    SELECT 
                        pg_roles.rolname
                    FROM pg_roles 
                    WHERE pg_has_role(current_user, pg_roles.oid, 'member');
                """)
                user_roles = [row[0] for row in cur.fetchall()]
                print(f"   Roles do usuário: {user_roles}")
                
            else:
                print("   ❌ Tabela raw_trips_landing NÃO encontrada!")
        else:
            print("   ❌ Schema bronze NÃO existe!")
        
        cur.close()
        conn.close()
        print("\n=== DIAGNÓSTICO CONCLUÍDO ===")
        
    except psycopg2.Error as e:
        print(f"❌ Erro de conexão: {e}")
        print(f"Código do erro: {e.pgcode}")
        if hasattr(e, 'pgerror'):
            print(f"Detalhe: {e.pgerror}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
