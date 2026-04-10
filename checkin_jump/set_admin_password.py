import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.get(username='admin')
u.set_password('admin123')
u.save()
print('✅ Senha definida com sucesso!')
print('   Usuário: admin')
print('   Senha: admin123')
