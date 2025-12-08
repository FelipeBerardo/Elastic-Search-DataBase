#!/usr/bin/env python3
# populate_missions.py - Popular Elasticsearch com dados de Missões

from elasticsearch import Elasticsearch, helpers
from datetime import datetime, timedelta
import random
import sys

print("🎯 Iniciando população de Missões...")
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
# DELETAR ÍNDICE EXISTENTE
# ============================================================
try:
    if es.indices.exists(index="rpg_missoes"):
        print("⚠️  Índice 'rpg_missoes' já existe")
        resposta = input("Deseja deletar e recriar? (s/N): ").lower()
        if resposta == 's':
            es.indices.delete(index="rpg_missoes")
            print("🗑️  Índice deletado")
        else:
            print("Usando índice existente...")
except Exception as e:
    print(f"Aviso ao verificar índice: {e}")

# ============================================================
# CRIAR ÍNDICE COM MAPPING
# ============================================================
print("\n📝 Criando índice 'rpg_missoes'...")

mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "mission_analyzer": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "titulo": {
                "type": "text",
                "analyzer": "mission_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "descricao": {"type": "text", "analyzer": "mission_analyzer"},
            "objetivo": {"type": "text"},
            "recompensa_ouro": {"type": "integer"},
            "recompensa_experiencia": {"type": "integer"},
            "nivel_minimo": {"type": "short"},
            "nivel_maximo": {"type": "short"},
            "dificuldade": {"type": "keyword"},
            "tipo": {"type": "keyword"},
            "localizacao": {"type": "keyword"},
            "status": {"type": "keyword"},
            "npc_ofertante": {"type": "keyword"},
            "tempo_limite_dias": {"type": "short"},
            "numero_aceitacoes": {"type": "integer"},
            "numero_conclusoes": {"type": "integer"},
            "taxa_conclusao_pct": {"type": "float"},
            "data_criacao": {"type": "date"},
            "repeticao_permitida": {"type": "boolean"}
        }
    }
}

try:
    if not es.indices.exists(index="rpg_missoes"):
        es.indices.create(index="rpg_missoes", body=mapping)
        print("✅ Índice criado com mapping")
    else:
        print("✅ Usando índice existente")
except Exception as e:
    print(f"⚠️  Aviso ao criar índice: {e}")

# ============================================================
# GERAR DADOS
# ============================================================
print("\n🎯 Gerando missões...")

tipos_missao = ["Eliminar", "Coletar", "Explorar", "Proteger", "Investigar", "Resgate", "Entrega", "Assassinato"]
dificuldades = ["Fácil", "Normal", "Difícil", "Muito Difícil", "Lendário"]
localizacoes = ["Floresta Escura", "Caverna Profunda", "Torre do Mago", "Ruínas Antigas", 
                "Castelo Abandonado", "Montanha Nevada", "Pântano Misterioso", "Cidade Perdida"]
npcs = ["Merlim", "Gandalf", "Bilbo", "Aragorn", "Galadriel", "Elrond", "Legolas", "Gimli"]

missoes_data = []

# Gerar 60 missões
for i in range(1, 61):
    tipo = random.choice(tipos_missao)
    dificuldade = random.choice(dificuldades)
    localizacao = random.choice(localizacoes)
    npc = random.choice(npcs)
    
    # Nível baseado na dificuldade
    if dificuldade == "Fácil":
        nivel_min = random.randint(1, 5)
        nivel_max = nivel_min + 3
        ouro = random.randint(50, 150)
        exp = random.randint(100, 300)
    elif dificuldade == "Normal":
        nivel_min = random.randint(5, 10)
        nivel_max = nivel_min + 3
        ouro = random.randint(200, 500)
        exp = random.randint(500, 1000)
    elif dificuldade == "Difícil":
        nivel_min = random.randint(10, 15)
        nivel_max = nivel_min + 3
        ouro = random.randint(800, 1500)
        exp = random.randint(1500, 3000)
    elif dificuldade == "Muito Difícil":
        nivel_min = random.randint(15, 18)
        nivel_max = nivel_min + 3
        ouro = random.randint(2000, 4000)
        exp = random.randint(4000, 6000)
    else:  # Lendário
        nivel_min = random.randint(18, 20)
        nivel_max = 20
        ouro = random.randint(5000, 10000)
        exp = random.randint(8000, 15000)
    
    # Taxa de conclusão varia conforme dificuldade
    if dificuldade == "Fácil":
        taxa = random.randint(70, 95)
    elif dificuldade == "Normal":
        taxa = random.randint(50, 75)
    elif dificuldade == "Difícil":
        taxa = random.randint(30, 60)
    elif dificuldade == "Muito Difícil":
        taxa = random.randint(10, 40)
    else:
        taxa = random.randint(1, 20)
    
    num_aceitacoes = random.randint(10, 500)
    num_conclusoes = int((num_aceitacoes * taxa) / 100)
    
    missao = {
        "titulo": f"{tipo} os {random.choice(['Orcs', 'Goblins', 'Dragões', 'Espectros', 'Mortos-Vivos', 'Feiticeiros'])} da {localizacao}",
        "descricao": f"Uma perigosa missão de {tipo.lower()} na {localizacao}. Oferecida por {npc}. Dificuldade: {dificuldade}",
        "objetivo": f"Completar a tarefa de {tipo.lower()} conforme solicitado",
        "recompensa_ouro": ouro,
        "recompensa_experiencia": exp,
        "nivel_minimo": nivel_min,
        "nivel_maximo": nivel_max,
        "dificuldade": dificuldade,
        "tipo": tipo,
        "localizacao": localizacao,
        "status": random.choice(["Ativa", "Inativa", "Concluída"]),
        "npc_ofertante": npc,
        "tempo_limite_dias": random.randint(3, 30),
        "numero_aceitacoes": num_aceitacoes,
        "numero_conclusoes": num_conclusoes,
        "taxa_conclusao_pct": taxa,
        "data_criacao": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
        "repeticao_permitida": random.choice([True, False])
    }
    
    missoes_data.append({
        "_index": "rpg_missoes",
        "_id": str(i),
        "_source": missao
    })

print(f"✅ {len(missoes_data)} missões geradas")

# ============================================================
# INSERIR DADOS
# ============================================================
print("\n📤 Inserindo dados no Elasticsearch...")

try:
    success, failed = helpers.bulk(es, missoes_data, stats_only=True)
    print(f"✅ {success} missões inseridas com sucesso")
    
    if failed > 0:
        print(f"⚠️  {failed} missões falharam")
        
except Exception as e:
    print(f"❌ Erro ao inserir dados: {e}")
    sys.exit(1)

# ============================================================
# REFRESH INDEX
# ============================================================
print("\n🔄 Atualizando índice...")
try:
    es.indices.refresh(index="rpg_missoes")
    print("✅ Índice atualizado")
except Exception as e:
    print(f"⚠️  Aviso ao atualizar: {e}")

# ============================================================
# VERIFICAR DADOS
# ============================================================
print("\n📊 Verificando dados inseridos...")

try:
    count_result = es.count(index="rpg_missoes")
    count = count_result['count']
    print(f"✅ Total de missões: {count}")
    
    search_result = es.search(
        index="rpg_missoes",
        body={"query": {"match_all": {}}, "size": 5}
    )
    
    print("\n📄 Exemplos de missões inseridas:")
    for hit in search_result['hits']['hits']:
        src = hit['_source']
        print(f"   ID {hit['_id']}: {src['titulo']} ({src['dificuldade']}, {src['recompensa_ouro']} ouro)")
    
except Exception as e:
    print(f"❌ Erro ao verificar: {e}")

print("\n" + "=" * 60)
print("🎉 População de missões concluída!")
print("=" * 60)
