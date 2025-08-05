# 🗄️ Conectar Banco PostgreSQL - Passo a Passo

## ✅ Instruções do Railway

O Railway está te mostrando exatamente como conectar o banco. Siga estes passos:

## 📋 **Passo 1: Criar Variável no Projeto Django**

### **No Railway Dashboard:**
1. **Vá para seu projeto Django**
2. **Clique em "Variables"**
3. **Clique em "New Variable"**
4. **Nome da variável**: `DATABASE_URL`
5. **Valor da variável**: `${{ Postgres.DATABASE_URL }}`
6. **Clique em "Add"**

## 📋 **Passo 2: Verificar Variáveis**

### **Confirme que estas variáveis estão configuradas:**
- ✅ `DATABASE_URL` = `${{ Postgres.DATABASE_URL }}`
- ✅ `SECRET_KEY` = sua chave secreta
- ✅ `DEBUG=False`

## 📋 **Passo 3: Configurar Comandos**

### **Custom Build Command:**
```bash
cd checkin_jump && pip install -r requirements.txt && python manage.py collectstatic --no-input
```

### **Custom Start Command:**
```bash
cd checkin_jump && python manage.py migrate --noinput && python manage.py loaddata backup_local.json && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

## 📋 **Passo 4: Fazer Deploy**

### **Opção A: Deploy Automático**
1. **O Railway fará deploy automático após salvar as variáveis**
2. **Monitore os logs**

### **Opção B: Deploy Manual**
1. **Clique em "Deploy"**
2. **Aguarde o build e deploy**

## 🎯 **O que acontecerá:**

1. **Build Phase:**
   - ✅ Instala dependências
   - ✅ Coleta arquivos estáticos

2. **Start Phase:**
   - ✅ Conecta ao banco PostgreSQL
   - ✅ Executa migrações
   - ✅ Carrega dados do backup
   - ✅ Inicia servidor

## 📊 **Logs Esperados:**

```
✅ Installing dependencies...
✅ Collecting static files...
✅ Running database migrations...
✅ Loading data from backup_local.json...
✅ Starting Gunicorn server...
```

## ✅ **Verificação Final:**

1. **Acesse a URL do Railway**
2. **Teste fazer login**
3. **Verifique se os dados estão lá:**
   - Lista de adolescentes
   - PGs criados
   - Impérios
   - Histórico de check-ins

## 🚨 **Se Houver Problemas:**

### **Erro de Conexão:**
- Verifique se `DATABASE_URL` está configurada corretamente
- Confirme se o valor é `${{ Postgres.DATABASE_URL }}`

### **Erro de Loaddata:**
- Verifique se o arquivo `backup_local.json` está no repositório
- Confirme se as migrações foram executadas primeiro

## 🎉 **Resultado:**

Após seguir estes passos, sua aplicação terá:
- ✅ Banco PostgreSQL conectado
- ✅ Todas as tabelas criadas
- ✅ Todos os seus dados transferidos
- ✅ Aplicação funcionando perfeitamente

**Siga exatamente as instruções do Railway e faça o deploy!** 🚀 