# Deploy no Render - Checkin Jump

## 📋 Pré-requisitos

1. Conta no Render.com
2. Projeto no GitHub/GitLab
3. Banco PostgreSQL (pode ser criado no Render)

## 🚀 Passos para Deploy

### 1. Preparar o Repositório

Certifique-se de que os seguintes arquivos estão no repositório:
- `requirements.txt`
- `build.sh`
- `runtime.txt`
- `config/settings_prod.py`

### 2. Criar Web Service no Render

1. Acesse [render.com](https://render.com)
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub/GitLab
4. Configure:

**Build Command:**
```bash
./build.sh
```

**Start Command:**
```bash
gunicorn config.wsgi:application
```

### 3. Configurar Variáveis de Ambiente

No painel do Render, vá em "Environment" e adicione:

```
DJANGO_SETTINGS_MODULE=config.settings_prod
POSTGRES_DB=checkin_jump
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_HOST=seu_host_postgres
POSTGRES_PORT=5432
SECRET_KEY=sua_chave_secreta_aqui
```

### 4. Configurar Banco PostgreSQL

1. Crie um banco PostgreSQL no Render
2. Copie as credenciais para as variáveis de ambiente
3. Execute as migrações automaticamente (já configurado no build.sh)

### 5. Configurar Domínio

- O Render fornecerá um domínio `.onrender.com`
- Configure `ALLOWED_HOSTS` no `settings_prod.py` se necessário

## 🔧 Configurações Importantes

### Static Files
- Configurado com WhiteNoise
- Coletados automaticamente no build

### Database
- PostgreSQL configurado via variáveis de ambiente
- Migrações executadas automaticamente

### Security
- DEBUG = False em produção
- Configurações de segurança ativadas

## 📝 Comandos Úteis

```bash
# Verificar logs
render logs

# Executar comando no servidor
render exec

# Fazer deploy manual
git push origin main
```

## 🐛 Troubleshooting

### Erro de Static Files
- Verifique se o WhiteNoise está instalado
- Confirme se `collectstatic` está sendo executado

### Erro de Database
- Verifique as variáveis de ambiente
- Confirme se o PostgreSQL está rodando

### Erro de Import
- Verifique se `DJANGO_SETTINGS_MODULE` está correto
- Confirme se todos os arquivos estão no repositório 