#!/usr/bin/env python3
# populate_elastic.py - Popular Elasticsearch com dados de RPG
from elasticsearch import Elasticsearch, helpers
from datetime import datetime
import random
import sys

print("🎲 Iniciando população do Elasticsearch...")
print("=" * 60)

# Conectar
es = Elasticsearch("http://localhost:9200")

# Verificar conexão
if not es.ping():
    print("❌ Elasticsearch não está rodando!")
    print("Execute: docker-compose up -d")
    sys.exit(1)

print("✅ Conectado ao Elasticsearch")

# ============================================================
# DELETAR ÍNDICE EXISTENTE (OPCIONAL)
# ============================================================
try:
    if es.indices.exists(index="rpg_itens"):
        print("⚠️  Índice 'rpg_itens' já existe")
        resposta = input("Deseja deletar e recriar? (s/N): ").lower()
        if resposta == 's':
            es.indices.delete(index="rpg_itens")
            print("🗑️  Índice deletado")
        else:
            print("Usando índice existente...")
except Exception as e:
    print(f"Aviso ao verificar índice: {e}")

# ============================================================
# CRIAR ÍNDICE COM MAPPING
# ============================================================
print("\n📝 Criando índice 'rpg_itens'...")

mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "item_analyzer": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "nome": {
                "type": "text",
                "analyzer": "item_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "completion"}
                }
            },
            "descricao": {"type": "text", "analyzer": "item_analyzer"},
            "tipo": {"type": "keyword"},
            "raridade": {"type": "keyword"},
            "valor": {"type": "integer"},
            "peso": {"type": "integer"},
            "nivel_requerido": {"type": "short"},
            "atributos_bonus": {
                "properties": {
                    "forca": {"type": "short"},
                    "destreza": {"type": "short"}
                }
            },
            "tags": {"type": "keyword"},
            "data_criacao": {"type": "date"}
        }
    }
}

try:
    if not es.indices.exists(index="rpg_itens"):
        es.indices.create(index="rpg_itens", body=mapping)
        print("✅ Índice criado com mapping")
    else:
        print("✅ Usando índice existente")
except Exception as e:
    print(f"⚠️  Aviso ao criar índice: {e}")

# ============================================================
# GERAR DADOS
# ============================================================
print("\n🎲 Gerando itens...")

# Listas para nomes
nomes_armas = ["Espada", "Machado", "Lança", "Martelo", "Adaga", "Arco", "Cajado", "Alabarda"]
adjetivos = ["Flamejante", "Gélida", "Sombria", "Radiante", "Venenosa", "Trovejante", "Ancestral", "Mística"]
tipos = ["Arma", "Armadura", "Acessório", "Consumível", "Livro", "Componente Arcano"]
raridades = ["Comum", "Incomum", "Raro", "Muito Raro", "Lendário", "Artefato"]

valor_por_raridade = {
    "Comum": (10, 100),
    "Incomum": (100, 500),
    "Raro": (500, 2000),
    "Muito Raro": (2000, 10000),
    "Lendário": (10000, 50000),
    "Artefato": (50000, 999999)
}

itens_data = []

# Gerar 100 itens
for i in range(1, 101):
    tipo = random.choice(tipos)
    raridade = random.choice(raridades)
    
    # Nome baseado no tipo
    if tipo == "Arma":
        nome_base = random.choice(nomes_armas)
        adjetivo = random.choice(adjetivos)
        nome = f"{nome_base} {adjetivo}"
    elif tipo == "Consumível":
        nome = f"Poção de {random.choice(['Cura', 'Força', 'Invisibilidade', 'Voo', 'Sabedoria'])}"
    elif tipo == "Livro":
        nome = f"Livro {random.choice(adjetivos)}"
    else:
        nome = f"{tipo} {random.choice(adjetivos)}"
    
    # Valor baseado na raridade
    valor_min, valor_max = valor_por_raridade[raridade]
    valor = random.randint(valor_min, valor_max)
    
    item = {
        "nome": nome,
        "descricao": f"Um {nome.lower()} de qualidade {raridade.lower()}",
        "tipo": tipo,
        "raridade": raridade,
        "valor": valor,
        "peso": random.randint(1, 50),
        "nivel_requerido": random.randint(1, 20),
        "tags": [tipo.lower(), raridade.lower()],
        "data_criacao": datetime.now().isoformat()
    }
    
    # Adicionar atributos bônus para armas/armaduras
    if tipo in ["Arma", "Armadura", "Acessório"]:
        item["atributos_bonus"] = {
            "forca": random.randint(0, 5),
            "destreza": random.randint(0, 5)
        }
    
    itens_data.append({
        "_index": "rpg_itens",
        "_id": str(i),
        "_source": item
    })

print(f"✅ {len(itens_data)} itens gerados")

# ============================================================
# INSERIR DADOS
# ============================================================
print("\n📤 Inserindo dados no Elasticsearch...")

try:
    # Bulk insert
    success, failed = helpers.bulk(es, itens_data, stats_only=True)
    print(f"✅ {success} itens inseridos com sucesso")
    
    if failed > 0:
        print(f"⚠️  {failed} itens falharam")
        
except Exception as e:
    print(f"❌ Erro ao inserir dados: {e}")
    sys.exit(1)

# ============================================================
# REFRESH INDEX
# ============================================================
print("\n🔄 Atualizando índice...")
try:
    es.indices.refresh(index="rpg_itens")
    print("✅ Índice atualizado")
except Exception as e:
    print(f"⚠️  Aviso ao atualizar: {e}")

# ============================================================
# VERIFICAR DADOS
# ============================================================
print("\n📊 Verificando dados inseridos...")

try:
    # Contar documentos
    count_result = es.count(index="rpg_itens")
    count = count_result['count']
    print(f"✅ Total de documentos: {count}")
    
    # Buscar alguns exemplos
    search_result = es.search(
        index="rpg_itens",
        body={
            "query": {"match_all": {}},
            "size": 5
        }
    )
    
    print("\n📄 Exemplos de itens inseridos:")
    for hit in search_result['hits']['hits']:
        src = hit['_source']
        print(f"   ID {hit['_id']}: {src['nome']} ({src['tipo']}, {src['raridade']}, {src['valor']} PO)")
    
    # Aggregation de teste
    agg_result = es.search(
        index="rpg_itens",
        body={
            "size": 0,
            "aggs": {
                "por_tipo": {"terms": {"field": "tipo"}},
                "por_raridade": {"terms": {"field": "raridade"}}
            }
        }
    )
    
    print("\n📊 Distribuição:")
    print("   Por tipo:")
    for bucket in agg_result['aggregations']['por_tipo']['buckets']:
        print(f"      {bucket['key']}: {bucket['doc_count']}")
    
    print("   Por raridade:")
    for bucket in agg_result['aggregations']['por_raridade']['buckets']:
        print(f"      {bucket['key']}: {bucket['doc_count']}")
    
except Exception as e:
    print(f"❌ Erro ao verificar: {e}")

# ============================================================
# TESTAR QUERIES
# ============================================================
print("\n🔍 Testando queries:")

try:
    # Teste 1: Buscar "espada"
    test1 = es.search(
        index="rpg_itens",
        body={
            "query": {
                "multi_match": {
                    "query": "espada",
                    "fields": ["nome", "descricao"]
                }
            },
            "size": 3
        }
    )
    print(f"✅ Busca 'espada': {test1['hits']['total']['value']} resultados")
    
    # Teste 2: Filtrar Arma Lendária
    test2 = es.search(
        index="rpg_itens",
        body={
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"tipo": "Arma"}},
                        {"term": {"raridade": "Lendário"}}
                    ]
                }
            }
        }
    )
    print(f"✅ Filtro 'Arma Lendária': {test2['hits']['total']['value']} resultados")
    
except Exception as e:
    print(f"❌ Erro nos testes: {e}")

# ============================================================
# FINALIZAR
# ============================================================
print("\n" + "=" * 60)
print("🎉 População concluída com sucesso!")
print("\n📝 Próximos passos:")
print("   1. Iniciar API: python app_rpg_search.py")
print("   2. Testar busca: curl 'http://localhost:5000/buscar?q=espada'")
print("   3. Ver Kibana: http://localhost:5601")
print("\n🔍 Para verificar dados:")
print("   python check_elastic.py")
print("=" * 60)