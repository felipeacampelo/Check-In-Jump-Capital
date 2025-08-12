# Sistema Check-in Jump

## 📋 Visão Geral do Projeto

O **Check-in Jump** é um sistema web desenvolvido para gerenciar a presença de adolescentes do JUMP, da Igreja Batista Capital, em eventos e celebrações. O sistema oferece uma solução completa para controle de frequência, organização por grupos e geração de relatórios estatísticos.

## 🎯 Visão do Projeto

### Missão
Facilitar o controle de presença e o acompanhamento de adolescentes em eventos e celebrações, proporcionando uma ferramenta moderna, intuitiva e eficiente.

### Objetivos Principais
- **Facilitar** o processo de check-in de adolescentes
- **Centralizar** informações de participantes em uma única plataforma
- **Gerar insights** através de dashboards e relatórios
- **Facilitar** a organização por pequenos grupos e impérios
- **Automatizar** a geração de relatórios de presença


## 🏗️ Arquitetura do Sistema

### Stack
- **Backend**: Django 5.2 (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Banco de Dados**: PostgreSQL
- **Deploy**: Railway Platform
- **Servidor Web**: Gunicorn + WhiteNoise


## 📊 Funcionalidades Principais

### 1. **Dashboard Administrativo**
- Visão geral de estatísticas
- Gráficos de presença por período
- Ranking de frequência por PG
- Métricas de engajamento

### 2. **Check-in**
- Interface otimizada para check-in rápido
- Busca por nome com sugestões
- Visualização de fotos para confirmação
- Status visual de presença

### 3. **Gestão de Eventos**
- Criação de eventos com títulos personalizados
- Controle de presença por evento
- Contagem de auditório
- Histórico completo de eventos

### 4. **Relatórios e Exportação**
- Exportação de dados de adolescentes
- Relatórios de presença por evento
- Dados em formato CSV para análise externa
- Filtros avançados por data e grupo

### 5. **Organização por Grupos**
- Gestão de Pequenos Grupos
- Visualização de membros por PG
- Estatísticas por PG

## 🚀 Benefícios do Sistema

### Para Líderes
- **Controle total** sobre presença e frequência
- **Insights valiosos** através de relatórios
- **Economia de tempo** no processo de check-in
- **Organização eficiente** 

### Para a Organização
- **Dados centralizados** e seguros
- **Acompanhamento** do engajamento dos adolescentes
- **Relatórios** para tomada de decisão
- **Escalabilidade** para crescimento futuro


## 🔄 Fluxo de Uso Padrão

1. **Cadastro Inicial**: Administrador cadastra adolescentes e organiza em PGs
2. **Criação de Evento**: Criação de nova celebração/evento
3. **Check-in**: Registro de presença durante o evento
4. **Monitoramento**: Acompanhamento em tempo real via dashboard
5. **Relatórios**: Geração de relatórios pós-evento
6. **Análise**: Uso de dados para melhorar engajamento

## 📈 Métricas

- **Taxa de presença média** por evento
- **Engajamento por Pequeno Grupo**
- **Crescimento de participação** ao longo do tempo
- **Eficiência do processo** de check-in


## 🔐 Permissões e Perfis de Acesso

### Perfis (Grupos) sugeridos
- **Admin**: acesso total (CRUD de todas as entidades, usuários e permissões).
- **Líder**: gerencia adolescentes, presença, eventos, PGs e Impérios; pode registrar contagens (auditório/visitantes) e exportar CSV.
- **Voluntário**: realiza check-in e visualiza listas; pode registrar contagens.

### Permissões por área (referência)
- Adolescentes: `add`, `change`, `delete`, `view` em `Adolescente`.
- Presenças: `add`, `change`, `delete`, `view` em `Presenca`.
- Dias de Evento: `add`, `change`, `delete`, `view` em `DiaEvento`.
- Contagens de Auditório: `add`, `change`, `delete`, `view` em `ContagemAuditorio`.
- Contagens de Visitantes: `add`, `change`, `delete`, `view` em `ContagemVisitantes`.
- Pequenos Grupos (PG): `add`, `change`, `delete`, `view` em `PG` (ou o nome do model correspondente).
- Impérios: `add`, `change`, `delete`, `view` em `Imperio` (ou o nome do model correspondente).
- Exportações: acesso às views de exportação (geralmente restritas a Líder/Admin).

> Observação: os nomes exatos dos models podem variar conforme definidos em `adolescentes/models.py`.

### Operações sensíveis
- Exclusão de registros (qualquer model).
- Edição retroativa de presenças e contagens.
- Criação/edição de usuários e permissões.

## 🛠️ Configuração e Deploy

O sistema está configurado para deploy automático na plataforma Railway, com:
- Build automatizado via `railway-build.sh`
- Configurações de produção otimizadas
- Servição de arquivos estáticos via WhiteNoise
- Banco de dados PostgreSQL em produção

---

**Versão**: 1.0  
**Última Atualização**: Agosto 2025  
**Desenvolvido para**: Jump Capital
**Tecnologia**: Django + PostgreSQL + Railway
