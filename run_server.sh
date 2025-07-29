#!/bin/bash
echo "🚀 Iniciando servidor Django..."
echo "📁 Diretório: $(pwd)"
echo "🐍 Python: $(which python)"
echo ""

# Ativar venv se não estiver ativo
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "🔧 Ativando ambiente virtual..."
    source venv/bin/activate
fi

echo "✅ Ambiente virtual ativo: $VIRTUAL_ENV"
echo "🌐 Servidor rodando em: http://127.0.0.1:8000/"
echo "⏹️  Para parar: Ctrl+C"
echo ""

python manage.py runserver 