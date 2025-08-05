# 🗄️ Transferir Banco Local para Railway - Passo a Passo

## 📋 **Passo 1: Fazer Dump do Banco Local**

### **No seu computador local:**
```bash
# Navegar para o diretório do projeto
cd /Users/felipecampelo/jump_project/checkin_jump

# Fazer dump do banco local
pg_dump -h localhost -U felipecampelo -d checkin_jump > backup_local.sql
```

### **Se pedir senha:**
- Digite a senha do seu PostgreSQL local
- Se não tiver senha, pressione Enter

## 📋 **Passo 2: Verificar o Arquivo de Backup**

### **Verificar se o dump foi criado:**
```bash
# Verificar se o arquivo existe
ls -la backup_local.sql

# Verificar o tamanho do arquivo
du -h backup_local.sql
```

## 📋 **Passo 3: Obter Credenciais do Railway**

### **No Railway Dashboard:**
1. **Vá para o banco PostgreSQL**
2. **Clique em "Connect"**
3. **Copie as credenciais:**
   - **Host**
   - **Port**
   - **Database**
   - **Username**
   - **Password**

## 📋 **Passo 4: Restaurar no Railway**

### **Opção A: Via Railway CLI (Recomendado)**
```bash
# Instalar Railway CLI (se não tiver)
npm install -g @railway/cli

# Login no Railway
railway login

# Conectar ao projeto
railway link

# Restaurar o banco
railway connect < backup_local.sql
```

### **Opção B: Via psql Direto**
```bash
# Usar as credenciais do Railway
psql -h [HOST_RAILWAY] -p [PORT] -U [USERNAME] -d [DATABASE] < backup_local.sql
```

### **Opção C: Via pgAdmin ou DBeaver**
1. **Conectar ao banco do Railway**
2. **Executar o script SQL do backup**

## 📋 **Passo 5: Verificar a Restauração**

### **No Railway Dashboard:**
1. **Vá para o banco PostgreSQL**
2. **Clique em "Query"**
3. **Execute:**
   ```sql
   SELECT COUNT(*) FROM adolescentes_adolescente;
   SELECT COUNT(*) FROM adolescentes_pequenogrupo;
   SELECT COUNT(*) FROM adolescentes_imperio;
   ```

## 📋 **Passo 6: Atualizar Configurações**

### **Verificar se as variáveis estão corretas:**
- ✅ `DATABASE_URL` - URL do Railway
- ✅ `SECRET_KEY` - Chave secreta
- ✅ `DEBUG=False`

## 📋 **Passo 7: Fazer Deploy**

### **Commit e push:**
```bash
git add .
git commit -m "Transfer database to Railway"
git push origin main
```

### **Verificar deploy:**
1. **Monitorar logs no Railway**
2. **Confirmar que as migrações não criaram conflitos**
3. **Testar a aplicação**

## 🚨 **Possíveis Problemas e Soluções**

### **Erro de Permissão:**
```bash
# Se der erro de permissão no dump
sudo -u postgres pg_dump -h localhost -U felipecampelo -d checkin_jump > backup_local.sql
```

### **Erro de Conexão:**
- Verificar se o PostgreSQL local está rodando
- Verificar credenciais locais

### **Erro de Restauração:**
- Verificar se o arquivo de backup está correto
- Verificar credenciais do Railway

### **Conflito de Migrações:**
```bash
# Se houver conflito, fazer fake migration
python manage.py migrate --fake-initial
```

## ✅ **Comandos Alternativos**

### **Dump com Formato Personalizado:**
```bash
pg_dump -h localhost -U felipecampelo -d checkin_jump -Fc > backup_local.dump
```

### **Restaurar Formato Personalizado:**
```bash
pg_restore -h [HOST_RAILWAY] -p [PORT] -U [USERNAME] -d [DATABASE] backup_local.dump
```

## 🎯 **Verificação Final**

### **Testar a aplicação:**
1. **Acesse a URL do Railway**
2. **Faça login**
3. **Verifique se os dados estão lá:**
   - Lista de adolescentes
   - PGs
   - Impérios
   - Histórico de check-ins

## 🎉 **Sucesso!**

Após seguir todos os passos, seu banco local estará transferido para o Railway e funcionando perfeitamente! 