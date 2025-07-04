
# 🧾 Checkin JUMP

Sistema web desenvolvido em Django para cadastro e check-in de adolescentes em eventos.

## ✅ Funcionalidades

- Cadastro de adolescentes com nome, sobrenome, foto, data de nascimento, gênero, PG e data de início
- Upload de foto
- Autenticação com login e logout
- Controle de permissões por tipo de usuário
- Dark mode
- Painel de administração Django
- Interface simples e responsiva com Bootstrap

---

## 🚀 Como rodar o projeto

- Clone o repositório:
git clone https://github.com/duduetca/checkin_jump_local
cd checkin_jump_local/checkin/checkin_jump

- Crie e ative um ambiente virtual (recomendado):
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

- Instale as dependências do projeto:
pip install -r requirements.txt

- Navegue até a pasta onde está o arquivo manage.py:
cd checkin_jump_local/checkin/checkin_jump

- Rode as migrations (para criar as tabelas no banco de dados):
python manage.py migrate

- Rode o servidor de desenvolvimento:
python manage.py runserver

- Acesse a aplicação no navegador:
http://127.0.0.1:8000/

### 1. Clone o repositório

**bash**
git clone https://github.com/l-chema/Projeto-Check-in.git
cd Projeto-Check-in


### 2. Crie e ative um ambiente virtual

#### Windows:
bash
python -m venv venv
venv\Scripts\activate


#### Linux/macOS:
bash
python3 -m venv venv
source venv/bin/activate


### 3. Instale as dependências

bash
pip install -r requirements.txt


### 4. Aplique as migrações

bash
python manage.py migrate


### 5. (Opcional) Crie um superusuário para acessar o admin

bash
python manage.py createsuperuser


### 6. Rode o servidor

bash
python manage.py runserver


Abra no navegador:  
`http://127.0.0.1:8000/`

---

## 🔒 Acesso ao Django Admin

Se tiver criado um superusuário, acesse:  
📎 `http://127.0.0.1:8000/admin/`

---

## 🗂 Estrutura básica do projeto

```
Projeto-Check-in/
│── checkin_jump/        # Configurações principais do projeto
│── adolescentes/        # App principal com modelos, views, templates, etc.
│── media/               # Onde as fotos dos adolescentes são armazenadas
│── static/              # Arquivos estáticos (CSS, JS)
│── requirements.txt     # Dependências do projeto
│── manage.py            # Entrada principal do Django
```

---

## 💡 Tecnologias utilizadas

- Python 3.12
- Django 5.2
- SQLite
- Bootstrap 5
- Git e GitHub

