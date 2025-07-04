# 🚀 Deploy no Render - Check-in JUMP

## ✅ Estrutura Reorganizada

O projeto foi reorganizado para seguir as melhores práticas do Django:

```
checkin_jump/
├── manage.py
├── requirements.txt
├── build.sh
├── runtime.txt
├── checkin_jump/          # Configurações do projeto
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── adolescentes/          # App principal
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── migrations/
│   ├── templates/
│   └── static/
├── static/               # Arquivos estáticos globais
├── media/               # Uploads de usuário
└── templates/           # Templates globais
```

## 🎯 Deploy no Render

### 1. **Criar Conta no Render**
- Acesse [render.com](https://render.com)
- Faça login com GitHub

### 2. **Criar Web Service**
- Clique em "New +" → "Web Service"
- Conecte seu repositório GitHub
- Selecione o repositório do projeto

### 3. **Configurações do Web Service**
```
Name: checkin-jump
Environment: Python 3
Build Command: ./build.sh
Start Command: gunicorn checkin_jump.wsgi:application
```

### 4. **Variáveis de Ambiente**
Adicione estas variáveis no Render:

```
DEBUG=False
SECRET_KEY=sua_chave_secreta_aqui
DATABASE_URL=postgresql://user:password@host:port/database
```

### 5. **Criar PostgreSQL Database**
- "New +" → "PostgreSQL"
- Escolha o plano Starter ($7/mês)
- Copie a DATABASE_URL gerada
- Cole nas variáveis de ambiente

## 🔧 Configurações Específicas

### **Build Command**
O arquivo `build.sh` já está configurado:
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

### **Start Command**
```bash
gunicorn checkin_jump.wsgi:application
```

### **Dependências**
O `requirements.txt` inclui:
- Django 5.2
- PostgreSQL (psycopg2-binary)
- WhiteNoise (arquivos estáticos)
- Gunicorn (servidor WSGI)

## 🛡️ Segurança

### **Configurações Automáticas**
- SSL/HTTPS automático
- Headers de segurança
- Cookies seguros
- CSRF protection

### **Variáveis de Ambiente**
- SECRET_KEY: Gere uma chave segura
- DEBUG: False em produção
- DATABASE_URL: Configurada pelo Render

## 📊 Monitoramento

### **Logs**
- Acesse "Logs" no dashboard do Render
- Monitore erros e performance

### **Métricas**
- Uso de RAM (deve ficar < 400MB)
- Tempo de resposta
- Número de requisições

## 🔄 Reversão

Se precisar voltar à estrutura antiga:
```bash
./reverter_organizacao.sh
```

## 🎉 Benefícios da Nova Estrutura

✅ **Padrão Django** - Estrutura profissional  
✅ **Deploy fácil** - Otimizado para Render  
✅ **Escalabilidade** - Fácil adicionar novos apps  
✅ **Manutenibilidade** - Código organizado  
✅ **Segurança** - Configurações de produção  

## 🚀 Próximos Passos

1. **Fazer commit** da nova estrutura
2. **Push para GitHub**
3. **Deploy no Render**
4. **Configurar domínio** (opcional)
5. **Monitorar performance**

---

**🎯 Resultado:** Sistema profissional pronto para produção! 