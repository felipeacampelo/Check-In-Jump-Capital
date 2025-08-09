import json

# Caminho do arquivo original
input_path = 'backup_local.json'

# Caminho do arquivo limpo que será criado
output_path = 'backup_local_clean.json'

# Abrir o JSON original
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Filtrar e manter só os objetos que não são do modelo auth.permission
clean_data = [obj for obj in data if obj.get('model') != 'auth.permission']

# Salvar o JSON limpo
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, indent=2, ensure_ascii=False)

print(f'Arquivo limpo salvo em: {output_path}')
