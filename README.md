# RPG Search - Sistema Completo de Gerenciamento

Uma aplicação completa para gerenciar **Itens**, **Personagens** e **Missões** de RPG usando Elasticsearch, Flask e Streamlit.

## 🎮 Características

### Módulo de Itens
- 🔍 Busca full-text por nome, descrição e tags
- 🎯 Filtros avançados por tipo, raridade e valor
- 📊 Dashboard analítico com estatísticas
- 🎁 Busca de itens similares
- 🔎 Busca avançada com múltiplos critérios

### Módulo de Personagens
- 🔍 Busca de personagens por nome, classe ou raça
- 🎯 Filtros por classe, raça, nível e status
- 📊 Dashboard com estatísticas de personagens
- 🏆 Top personagens por nível, experiência ou força
- 📈 Análise de distribuição de classes e raças

### Módulo de Missões
- 🔍 Busca de missões por título, tipo ou objetivo
- 🎯 Filtros por dificuldade, tipo, nível e recompensa
- 📊 Dashboard com análises de missões
- 🏆 Visualização de missões por nível de dificuldade
- 💰 Análise de recompensas e taxas de conclusão

## 📦 Requisitos

### Dependências Python
```bash
pip install elasticsearch flask streamlit plotly pandas requests
```

### Serviços
- Docker e Docker Compose (para Elasticsearch)

## 🚀 Instalação e Execução

### 1. Iniciar Elasticsearch
```bash
docker-compose up -d
```

Aguarde até que o Elasticsearch esteja pronto (cerca de 10-15 segundos).

### 2. Popular Bancos de Dados

#### Popular Itens
```bash
python populate_elastic.py
```

#### Popular Personagens
```bash
python populate_characters.py
```

#### Popular Missões
```bash
python populate_missions.py
```

### 3. Iniciar a API Flask
```bash
python app_rpg_search.py
```

A API estará disponível em: `http://localhost:5000`

### 4. Iniciar o Frontend Web (Streamlit)
Em outro terminal:
```bash
streamlit run frontend_web_rpg.py
```

A aplicação web abrirá em: `http://localhost:8501`

## 📊 Estrutura de Dados

### Índice: rpg_itens
- **nome**: Nome do item
- **descricao**: Descrição detalhada
- **tipo**: Arma, Armadura, Acessório, Consumível, Livro, Componente Arcano
- **raridade**: Comum, Incomum, Raro, Muito Raro, Lendário, Artefato
- **valor**: Preço em ouro (PO)
- **peso**: Peso do item
- **nivel_requerido**: Nível mínimo para usar
- **tags**: Tags para categorização

### Índice: rpg_personagens
- **nome**: Nome do personagem
- **classe**: Guerreiro, Mago, Assassino, Paladino, Ranger, Bardo, Druida, Clérigo
- **raca**: Humano, Elfo, Anão, Gnomo, Meio-Orc, Meio-Elfo, Tiefling, Dracônico
- **nivel**: Nível do personagem (1-20)
- **experiencia**: Pontos de experiência acumulados
- **vida**: Pontos de vida máximos
- **mana**: Pontos de mana (se aplicável)
- **atributos**: Força, Destreza, Constituição, Inteligência, Sabedoria, Carisma
- **status**: Ativo, Inativo, Morto, Congelado

### Índice: rpg_missoes
- **titulo**: Título da missão
- **descricao**: Descrição detalhada
- **objetivo**: Objetivo da missão
- **tipo**: Eliminar, Coletar, Explorar, Proteger, Investigar, Resgate, Entrega, Assassinato
- **dificuldade**: Fácil, Normal, Difícil, Muito Difícil, Lendário
- **localizacao**: Local onde a missão ocorre
- **nivel_minimo/maximo**: Faixa de nível recomendada
- **recompensa_ouro**: Ouro a ganhar
- **recompensa_experiencia**: XP a ganhar
- **taxa_conclusao_pct**: Percentual de conclusão
- **npc_ofertante**: NPC que oferece a missão

## 🌐 Endpoints da API

### Itens
- `GET /buscar?q=termo` - Busca full-text
- `POST /filtrar` - Filtros combinados
- `GET /autocomplete?q=prefixo` - Sugestões
- `GET /similares/<id>` - Itens similares
- `GET /dashboard` - Dashboard de itens
- `POST /busca-avancada` - Busca avançada

### Personagens
- `GET /buscar_personagens?q=termo` - Busca de personagens
- `POST /filtrar_personagens` - Filtrar personagens
- `GET /dashboard_personagens` - Dashboard de personagens
- `GET /top_personagens?ordenar_por=nivel` - Top personagens

### Missões
- `GET /buscar_missoes?q=termo` - Busca de missões
- `POST /filtrar_missoes` - Filtrar missões
- `GET /dashboard_missoes` - Dashboard de missões
- `GET /missoes_dificuldade?dificuldade=Normal` - Missões por dificuldade

## 💾 Arquivos do Projeto

```
├── docker-compose.yaml          # Configuração do Elasticsearch
├── populate_elastic.py          # Popular itens
├── populate_characters.py       # Popular personagens
├── populate_missions.py         # Popular missões
├── app_rpg_search.py            # API Flask
├── frontend_rpg.py              # Frontend terminal (opcional)
├── frontend_web_rpg.py          # Frontend web (Streamlit)
├── check_elastic.py             # Verificar status
└── test_api.sh                  # Testes da API
```

## 🎯 Casos de Uso

### Exemplo 1: Encontrar Equipamento Poderoso
1. Acesse "Itens" → "Filtros"
2. Selecione "Lendário" em Raridade
3. Configure valor mínimo alto
4. Veja os itens mais poderosos

### Exemplo 2: Recrutar um Personagem
1. Acesse "Personagens" → "Filtrar Personagens"
2. Selecione classe "Mago"
3. Configure nível mínimo
4. Veja os magos disponíveis

### Exemplo 3: Aceitar Missões Apropriadas
1. Acesse "Missões" → "Filtrar Missões"
2. Configure dificuldade e nível
3. Veja as recompensas em ouro e XP
4. Aceite a missão

## 🔍 Exemplos de Busca

### Terminal / cURL
```bash
# Buscar itens
curl "http://localhost:5000/buscar?q=espada"

# Filtrar por raridade
curl -X POST "http://localhost:5000/filtrar" \
  -H "Content-Type: application/json" \
  -d '{"raridade":"Lendário"}'

# Dashboard
curl "http://localhost:5000/dashboard"

# Buscar personagens
curl "http://localhost:5000/buscar_personagens?q=Mago"

# Buscar missões
curl "http://localhost:5000/buscar_missoes?q=Dragão"
```

## 📊 Visualizações

A aplicação web oferece:
- 📈 Gráficos de barras para distribuições
- 🥧 Gráficos de pizza para proporções
- 📊 Tabelas interativas com dados
- 💹 Métricas em destaque
- 🎯 Filtros dinâmicos em tempo real

## 🛠️ Troubleshooting

### Elasticsearch não inicia
```bash
docker-compose down
docker-compose up -d
```

### Dados não aparecem
```bash
# Verificar status
python check_elastic.py

# Re-popular dados
python populate_elastic.py
python populate_characters.py
python populate_missions.py
```

### API não conecta
- Verifique se a API Flask está rodando em `http://localhost:5000`
- Verifique se o Elasticsearch está ativo em `http://localhost:9200`

### Streamlit não abre a aba
```bash
# Reinstale streamlit
pip install --upgrade streamlit
```

## 📝 Notas

- O banco de dados é gerado aleatoriamente a cada execução
- Os personagens têm atributos baseados em suas classes
- As missões têm recompensas baseadas em dificuldade
- Todos os dados são persistidos no Elasticsearch
- O frontend é totalmente responsivo

## 🎮 Diversão!

Explore os diferentes módulos, experimente as buscas, crie estratégias baseadas nas análises. A aplicação oferece uma experiência completa de gerenciamento de RPG!

---

**Desenvolvido com ❤️ para gerenciar aventuras épicas!**
