#!/usr/bin/env python3
"""
Script para debug de problemas no Railway
"""

import os
import sys
import django

def check_environment():
    """Verifica as variáveis de ambiente"""
    print("🔍 Verificando variáveis de ambiente...")
    
    required_vars = ['DATABASE_URL', 'SECRET_KEY', 'DEBUG']
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            if var == 'SECRET_KEY':
                print(f"✅ {var}: {'*' * 10}...{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NÃO CONFIGURADA")
    
    print(f"✅ PORT: {os.environ.get('PORT', 'NÃO DEFINIDA')}")

def check_django_setup():
    """Verifica se o Django consegue inicializar"""
    print("\n🔍 Verificando configuração do Django...")
    
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.conf import settings
        print("✅ Django inicializado com sucesso")
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"✅ DATABASES: {list(settings.DATABASES.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao inicializar Django: {e}")
        return False

def check_database():
    """Verifica conexão com o banco de dados"""
    print("\n🔍 Verificando conexão com banco de dados...")
    
    try:
        from django.db import connection
        from django.db.utils import OperationalError
        
        # Testar conexão
        connection.ensure_connection()
        print("✅ Conexão com banco de dados OK")
        
        # Verificar se as tabelas existem
        from django.apps import apps
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"✅ Tabelas encontradas: {len(tables)}")
            if tables:
                print(f"   Primeiras tabelas: {tables[:5]}")
        
        return True
    except OperationalError as e:
        print(f"❌ Erro de conexão com banco: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return False

def check_static_files():
    """Verifica arquivos estáticos"""
    print("\n🔍 Verificando arquivos estáticos...")
    
    try:
        from django.conf import settings
        from django.contrib.staticfiles.finders import find
        
        # Verificar se o diretório staticfiles existe
        static_root = settings.STATIC_ROOT
        if os.path.exists(static_root):
            print(f"✅ STATIC_ROOT existe: {static_root}")
            files = os.listdir(static_root)
            print(f"   Arquivos encontrados: {len(files)}")
        else:
            print(f"❌ STATIC_ROOT não existe: {static_root}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar arquivos estáticos: {e}")
        return False

def check_models():
    """Verifica se os modelos estão funcionando"""
    print("\n🔍 Verificando modelos...")
    
    try:
        from adolescentes.models import Adolescente, PequenoGrupo, Imperio
        
        # Contar registros
        total_adolescentes = Adolescente.objects.count()
        total_pgs = PequenoGrupo.objects.count()
        total_imperios = Imperio.objects.count()
        
        print(f"✅ Adolescente.objects.count(): {total_adolescentes}")
        print(f"✅ PequenoGrupo.objects.count(): {total_pgs}")
        print(f"✅ Imperio.objects.count(): {total_imperios}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar modelos: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Debug do Railway - Check-in JUMP")
    print("=" * 50)
    
    # Verificar ambiente
    check_environment()
    
    # Verificar Django
    if not check_django_setup():
        print("\n❌ Falha na configuração do Django")
        return
    
    # Verificar banco de dados
    if not check_database():
        print("\n❌ Falha na conexão com banco de dados")
        return
    
    # Verificar arquivos estáticos
    check_static_files()
    
    # Verificar modelos
    if not check_models():
        print("\n❌ Falha nos modelos")
        return
    
    print("\n" + "=" * 50)
    print("🎉 TUDO OK! A aplicação deve estar funcionando.")
    print("\n📋 URLs disponíveis:")
    print("- /login/ - Página de login")
    print("- /adolescentes/ - Lista de adolescentes")
    print("- /checkin/ - Página de check-in")
    print("- /dashboard/ - Dashboard")
    print("- /admin/ - Admin do Django")

if __name__ == "__main__":
    main() 