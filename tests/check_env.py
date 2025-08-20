"""
Verifica se as variáveis de ambiente estão sendo carregadas corretamente
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=== VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE ===")
print(f"PG_HOST: '{os.getenv('PG_HOST', 'NÃO DEFINIDO')}'")
print(f"PG_PORT: '{os.getenv('PG_PORT', 'NÃO DEFINIDO')}'")
print(f"PG_DATABASE: '{os.getenv('PG_DATABASE', 'NÃO DEFINIDO')}'")
print(f"PG_USER: '{os.getenv('PG_USER', 'NÃO DEFINIDO')}'")
print(f"PG_PASSWORD: '{'*' * len(os.getenv('PG_PASSWORD', '')) if os.getenv('PG_PASSWORD') else 'NÃO DEFINIDO'}'")

# Verifica se arquivo .env existe
if os.path.exists('.env'):
    print("\n✅ Arquivo .env encontrado")
    with open('.env', 'r') as f:
        lines = f.readlines()
    print(f"Linhas no .env: {len(lines)}")
    print("Conteúdo (sem senhas):")
    for line in lines:
        if 'PASSWORD' not in line.upper():
            print(f"  {line.strip()}")
        else:
            print(f"  {line.split('=')[0]}=***")
else:
    print("❌ Arquivo .env NÃO encontrado")
