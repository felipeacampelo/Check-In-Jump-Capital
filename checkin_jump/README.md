# Sistema Check-in Jump - Documentação Técnica

## 📋 Visão Geral do Projeto

O **Check-in Jump** é um sistema web desenvolvido para gerenciar a presença de adolescentes do JUMP em eventos e celebrações. O sistema oferece uma solução completa para controle de frequência, organização por grupos e geração de relatórios estatísticos.

## 🎯 Visão do Projeto

### Missão
Facilitar o controle de presença e o acompanhamento de adolescentes em  eventos e celebrações, proporcionando uma ferramenta moderna, intuitiva e eficiente.

### Objetivos Principais
- **Facilitar** o processo de check-in de adolescentes
- **Centralizar** informações de participantes em uma única plataforma
- **Gerar insights** através de dashboards e relatórios
- **Facilitar** a organização por pequenos grupos e impérios
- **Automatizar** a geração de relatórios de presença

## ⚙️ Requisitos Funcionais

### 1. Gerenciamento de Adolescentes
- **RF01**: Cadastrar adolescentes com dados pessoais completos
- **RF02**: Armazenar foto de perfil de cada adolescente
- **RF03**: Organizar adolescentes por Pequenos Grupos (PGs)
- **RF04**: Categorizar adolescentes por Impérios
- **RF05**: Registrar data da primeira visita
- **RF06**: Editar e excluir registros de adolescentes
- **RF07**: Buscar adolescentes por nome (busca inteligente)
- **RF08**: Buscar adolescentes por meio de filtros

### 2. Sistema de Check-in
- **RF09**: Criar eventos/celebrações com datas específicas
- **RF10**: Realizar check-in individual de adolescentes
- **RF11**: Registrar contagem de auditório
- **RF12**: Visualizar status de presença em tempo real
- **RF13**: Atualizar presença via interface web

### 3. Dashboard e Relatórios
- **RF14**: Exibir estatísticas gerais de presença
- **RF15**: Gerar gráficos de frequência por período
- **RF16**: Mostrar frequência por PG
- **RF17**: Calcular médias de presença
- **RF18**: Exportar dados em formato CSV
- **RF19**: Filtrar relatórios por data e grupo

### 4. Gestão de Pequenos Grupos
- **RF20**: Criar e gerenciar Pequenos Grupos
- **RF21**: Visualizar detalhes e membros de cada PG
- **RF22**: Associar adolescentes a PGs específicos

### 5. Gestão de Impérios
- **RF23**: Criar e gerenciar Impérios
- **RF24**: Visualizar detalhes e membros de cada Império
- **RF25**: Associar adolescentes a Impérios específicos

### 6. Sistema de Autenticação
- **RF26**: Login seguro para usuários autorizados
- **RF27**: Controle de permissões por usuário
- **RF28**: Logout seguro do sistema

## 🔧 Requisitos Não Funcionais

### Performance
- **RNF01**: Sistema deve suportar até 2500 adolescentes cadastrados
- **RNF02**: Tempo de resposta inferior a 2 segundos para operações básicas
- **RNF03**: Interface responsiva para dispositivos móveis

### Segurança
- **RNF04**: Autenticação obrigatória para acesso ao sistema
- **RNF05**: Controle de permissões baseado em usuário
- **RNF06**: Proteção contra ataques CSRF

### Usabilidade
- **RNF07**: Interface intuitiva e amigável
- **RNF08**: Busca inteligente por nome completo
- **RNF09**: Feedback visual para ações do usuário

### Confiabilidade
- **RNF10**: Backup automático de dados
- **RNF11**: Logs de auditoria para alterações
- **RNF12**: Recuperação de dados em caso de falha

## 🏗️ Arquitetura do Sistema

### Stack Tecnológica
- **Backend**: Django 5.2 (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Banco de Dados**: PostgreSQL
- **Deploy**: Railway Platform
- **Servidor Web**: Gunicorn + WhiteNoise

### Estrutura de Dados Principais

#### Adolescente
- Nome e sobrenome
- Foto de perfil
- Data de nascimento
- Gênero (M/F)
- Pequeno Grupo associado
- Império associado
- Data de início na organização

#### Evento/Celebração
- Data do evento
- Título da celebração
- Registros de presença associados

#### Presença
- Adolescente
- Dia do evento
- Status de presença
- Horário de check-in

#### Pequeno Grupo
- Nome do grupo
- Gênero do grupo
- Lista de adolescentes

## 📊 Funcionalidades Principais

### 1. **Dashboard Administrativo**
- Visão geral de estatísticas
- Gráficos de presença por período
- Ranking de frequência por PG
- Métricas de engajamento

### 2. **Check-in Inteligente**
- Interface otimizada para check-in rápido
- Busca por nome com sugestões
- Visualização de fotos para confirmação
- Status visual de presença

### 3. **Gestão de Eventos**
- Criação de eventos com títulos personalizados
- Controle de presença por evento
- Contagem de auditório para eventos grandes
- Histórico completo de eventos

### 4. **Relatórios e Exportação**
- Exportação de dados de adolescentes
- Relatórios de presença por evento
- Dados em formato CSV para análise externa
- Filtros avançados por data e grupo

### 5. **Organização por Grupos**
- Gestão de Pequenos Grupos
- Visualização de membros por PG
- Estatísticas por grupo
- Organização hierárquica por Impérios

## 🚀 Benefícios do Sistema

### Para Líderes
- **Controle total** sobre presença e frequência
- **Insights valiosos** através de relatórios
- **Economia de tempo** no processo de check-in
- **Organização eficiente** por grupos

### Para a Organização
- **Dados centralizados** e seguros
- **Acompanhamento** do engajamento dos adolescentes
- **Relatórios** para tomada de decisão
- **Escalabilidade** para crescimento futuro


## 🔄 Fluxo de Uso Típico

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
