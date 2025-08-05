#!/usr/bin/env python3
"""
Script para verificar se a configuração do Railway está correta
"""

import os
import sys
from pathlib import Path

def check_file_exists(filename):
    """Verifica se um arquivo existe"""
    if Path(filename).exists():
        print(f"✅ {filename} - OK")
        return True
    else:
        print(f"❌ {filename} - FALTANDO")
        return False

def check_requirements():
    """Verifica se o requirements.txt tem as dependências necessárias"""
    required_packages = [
        'Django',
        'gunicorn',
        'dj-database-url',
        'psycopg2-binary',
        'whitenoise'
    ]
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            
        missing = []
        for package in required_packages:
            if package.lower() not in content.lower():
                missing.append(package)
        
        if missing:
            print(f"❌ requirements.txt - FALTANDO: {', '.join(missing)}")
            return False
        else:
            print("✅ requirements.txt - OK")
            return True
    except FileNotFoundError:
        print("❌ requirements.txt - ARQUIVO NÃO ENCONTRADO")
        return False

def check_settings():
    """Verifica se as configurações do Django estão corretas"""
    try:
        # Simula as configurações do Railway
        os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
        os.environ['DEBUG'] = 'False'
        os.environ['SECRET_KEY'] = 'test-key'
        
        # Importa as configurações
        import django
        django.setup()
        
        from django.conf import settings
        
        # Verifica configurações importantes
        checks = [
            ('DEBUG', settings.DEBUG == False, "DEBUG deve ser False em produção"),
            ('ALLOWED_HOSTS', '.railway.app' in settings.ALLOWED_HOSTS, "ALLOWED_HOSTS deve incluir .railway.app"),
            ('STATIC_ROOT', hasattr(settings, 'STATIC_ROOT'), "STATIC_ROOT deve estar configurado"),
            ('MIDDLEWARE', 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE, "WhiteNoise deve estar no MIDDLEWARE"),
        ]
        
        all_ok = True
        for name, check, message in checks:
            if check:
                print(f"✅ {name} - OK")
            else:
                print(f"❌ {name} - {message}")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"❌ Erro ao verificar configurações: {e}")
        return False

def main():
    """Função principal"""
    print("🔍 Verificando configuração do Railway...\n")
    
    # Verifica arquivos necessários
    required_files = [
        'railway.json',
        'Procfile',
        'railway-build.sh',
        'requirements.txt',
        'runtime.txt',
        'nixpacks.toml'
    ]
    
    files_ok = all(check_file_exists(f) for f in required_files)
    
    print("\n📦 Verificando dependências...")
    requirements_ok = check_requirements()
    
    print("\n⚙️ Verificando configurações do Django...")
    settings_ok = check_settings()
    
    print("\n" + "="*50)
    if files_ok and requirements_ok and settings_ok:
        print("🎉 TUDO PRONTO PARA DEPLOY NO RAILWAY!")
        print("\n📋 Próximos passos:")
        print("1. Faça commit das mudanças")
        print("2. Push para o GitHub")
        print("3. Conecte o repositório no Railway")
        print("4. Configure as variáveis de ambiente")
        print("5. Deploy!")
    else:
        print("⚠️ ALGUNS PROBLEMAS ENCONTRADOS")
        print("Verifique os erros acima antes do deploy")
    
    print("="*50)

if __name__ == "__main__":
    main() 