# 🚀 Deploy no Railway - Check-in JUMP

## ✅ Configuração para Railway

O projeto foi configurado para deploy no Railway com os seguintes arquivos:

### Arquivos de Configuração
- `railway.json` - Configuração do Railway
- `Procfile` - Comando de inicialização
- `railway-build.sh` - Script de build
- `requirements.txt` - Dependências Python
- `runtime.txt` - Versão do Python

## 🎯 Passos para Deploy

### 1. **Criar Conta no Railway**
- Acesse [railway.app](https://railway.app)
- Faça login com GitHub

### 2. **Criar Novo Projeto**
- Clique em "New Project"
- Selecione "Deploy from GitHub repo"
- Escolha seu repositório

### 3. **Configurar Variáveis de Ambiente**
No Railway Dashboard, adicione estas variáveis:

```
DEBUG=False
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=postgresql://user:password@host:port/database
```

### 4. **Criar PostgreSQL Database**
- No projeto Railway, clique em "New"
- Selecione "Database" → "PostgreSQL"
- O Railway criará automaticamente a DATABASE_URL

### 5. **Configurar Build**
O Railway detectará automaticamente:
- **Build Command**: `./railway-build.sh`
- **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

## 🔧 Configurações Específicas

### **Railway.json**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### **Procfile**
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### **Railway Build Script**
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

## 🛡️ Segurança

### **Configurações Automáticas**
- SSL/HTTPS automático
- Headers de segurança
- Cookies seguros
- CSRF protection
- HSTS habilitado

### **Variáveis de Ambiente Obrigatórias**
- `SECRET_KEY`: Chave secreta do Django
- `DATABASE_URL`: URL do PostgreSQL
- `DEBUG`: False em produção

## 📊 Monitoramento

O Railway oferece:
- Logs em tempo real
- Métricas de performance
- Monitoramento de saúde
- Deploy automático

## 🔄 Deploy Automático

O Railway fará deploy automático quando:
- Push para branch principal
- Pull request mergeado
- Deploy manual solicitado

## 🚨 Troubleshooting

### **Problemas Comuns**
1. **Build falha**: Verificar `requirements.txt`
2. **Migração falha**: Verificar `DATABASE_URL`
3. **Static files**: Verificar `collectstatic`
4. **Port binding**: Verificar `$PORT` no Procfile

### **Logs**
- Acesse os logs no Railway Dashboard
- Use `railway logs` no CLI
- Verifique logs de build e runtime

## 📝 Comandos Úteis

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login no Railway
railway login

# Deploy manual
railway up

# Ver logs
railway logs

# Abrir projeto
railway open
``` 