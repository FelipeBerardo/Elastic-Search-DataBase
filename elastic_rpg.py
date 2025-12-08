# elastic_rpg.py
from elasticsearch import Elasticsearch
from datetime import datetime

# Conectar
es = Elasticsearch("http://localhost:9200")

# Verificar conexão
if es.ping():
    print("✅ Conectado ao Elasticsearch!")
else:
    print("❌ Falha na conexão")
    exit()

# 1. Inserir documento
def criar_personagem(nome, classe, raca, nivel):
    doc = {
        "nome": nome,
        "classe": classe,
        "raca": raca,
        "nivel": nivel,
        "data_criacao": datetime.now(),
        "ativo": True
    }
    
    resp = es.index(index="rpg_personagens", document=doc)
    print(f"Personagem criado: {resp['_id']}")
    return resp['_id']

# 2. Buscar por nome
def buscar_personagem(nome):
    query = {
        "query": {
            "match": {
                "nome": nome
            }
        }
    }
    
    resp = es.search(index="rpg_personagens", body=query)
    print(f"\n🔍 Encontrados {resp['hits']['total']['value']} personagens:")
    
    for hit in resp['hits']['hits']:
        print(f"  - {hit['_source']['nome']} ({hit['_source']['classe']})")
    
    return resp['hits']['hits']

# 3. Filtrar por classe
def filtrar_por_classe(classe):
    query = {
        "query": {
            "term": {
                "classe": classe
            }
        }
    }
    
    resp = es.search(index="rpg_personagens", body=query)
    return resp['hits']['hits']

# 4. Atualizar documento
def atualizar_nivel(personagem_id, novo_nivel):
    es.update(
        index="rpg_personagens",
        id=personagem_id,
        body={"doc": {"nivel": novo_nivel}}
    )
    print(f"✅ Nível atualizado para {novo_nivel}")

# 5. Deletar documento
def deletar_personagem(personagem_id):
    es.delete(index="rpg_personagens", id=personagem_id)
    print(f"🗑️  Personagem {personagem_id} deletado")

# 6. Aggregation - Estatísticas
def estatisticas_gerais():
    query = {
        "size": 0,
        "aggs": {
            "por_classe": {
                "terms": {"field": "classe"}
            },
            "media_nivel": {
                "avg": {"field": "nivel"}
            },
            "total_xp": {
                "sum": {"field": "experiencia"}
            }
        }
    }
    
    resp = es.search(index="rpg_personagens", body=query)
    
    print("\n📊 Estatísticas:")
    print(f"  Média de nível: {resp['aggregations']['media_nivel']['value']:.1f}")
    print(f"  Total XP: {resp['aggregations']['total_xp']['value']}")
    print("\n  Personagens por classe:")
    for bucket in resp['aggregations']['por_classe']['buckets']:
        print(f"    {bucket['key']}: {bucket['doc_count']}")

# Executar exemplos
if __name__ == "__main__":
    # Buscar
    buscar_personagem("Grog")
    
    # Estatísticas
    estatisticas_gerais()
    
    # Criar novo
    novo_id = criar_personagem("Teste Warrior", "Guerreiro", "Humano", 5)
    
    # Atualizar
    atualizar_nivel(novo_id, 6)
    
    # Deletar
    deletar_personagem(novo_id)