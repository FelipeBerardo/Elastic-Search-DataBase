#!/usr/bin/env python3
# populate_characters.py - Popular Elasticsearch com dados de Personagens

from elasticsearch import Elasticsearch, helpers
from datetime import datetime
import random
import sys

print("🎭 Iniciando população de Personagens...")
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
    if es.indices.exists(index="rpg_personagens"):
        print("⚠️  Índice 'rpg_personagens' já existe")
        resposta = input("Deseja deletar e recriar? (s/N): ").lower()
        if resposta == 's':
            es.indices.delete(index="rpg_personagens")
            print("🗑️  Índice deletado")
        else:
            print("Usando índice existente...")
except Exception as e:
    print(f"Aviso ao verificar índice: {e}")

# ============================================================
# CRIAR ÍNDICE COM MAPPING
# ============================================================
print("\n📝 Criando índice 'rpg_personagens'...")

mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "character_analyzer": {
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
                "analyzer": "character_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "descricao": {"type": "text", "analyzer": "character_analyzer"},
            "classe": {"type": "keyword"},
            "raca": {"type": "keyword"},
            "nivel": {"type": "short"},
            "experiencia": {"type": "integer"},
            "vida": {"type": "short"},
            "mana": {"type": "short"},
            "forca": {"type": "short"},
            "destreza": {"type": "short"},
            "constituicao": {"type": "short"},
            "inteligencia": {"type": "short"},
            "sabedoria": {"type": "short"},
            "carisma": {"type": "short"},
            "status": {"type": "keyword"},
            "data_criacao": {"type": "date"},
            "ultima_atualizacao": {"type": "date"}
        }
    }
}

try:
    if not es.indices.exists(index="rpg_personagens"):
        es.indices.create(index="rpg_personagens", body=mapping)
        print("✅ Índice criado com mapping")
    else:
        print("✅ Usando índice existente")
except Exception as e:
    print(f"⚠️  Aviso ao criar índice: {e}")

# ============================================================
# GERAR DADOS
# ============================================================
print("\n🎭 Gerando personagens...")

classes = ["Guerreiro", "Mago", "Assassino", "Paladino", "Ranger", "Bardo", "Druida", "Clérigo"]
racas = ["Humano", "Elfo", "Anão", "Gnomo", "Meio-Orc", "Meio-Elfo", "Tiefling", "Dracônico"]
status = ["Ativo", "Inativo", "Morto", "Congelado"]

nomes_base = ["Aragorn", "Legolas", "Gandalf", "Gimli", "Frodo", "Bilbo", "Thorin", "Boromir", 
              "Galadriel", "Elrond", "Saruman", "Sauron", "Glorfindel", "Tauriel", "Thranduil"]

personagens_data = []

# Gerar 50 personagens
for i in range(1, 51):
    classe = random.choice(classes)
    raca = random.choice(racas)
    nivel = random.randint(1, 20)
    
    # Nome aleatório
    primeiro_nome = random.choice(nomes_base)
    sobrenome = random.choice(["o Bravo", "o Sábio", "o Rápido", "o Forte", "o Misterioso", "do Vale"])
    nome = f"{primeiro_nome} {sobrenome}"
    
    # Experiência baseada no nível
    exp = nivel * 1000 + random.randint(0, 500)
    
    # Atributos baseados na classe
    if classe == "Guerreiro":
        vida = 12 + (nivel * 2)
        forca = random.randint(16, 20)
        destreza = random.randint(10, 14)
        constituicao = random.randint(14, 18)
        inteligencia = random.randint(8, 12)
        sabedoria = random.randint(10, 14)
        carisma = random.randint(8, 12)
        mana = 0
    elif classe == "Mago":
        vida = 6 + (nivel * 1)
        forca = random.randint(8, 12)
        destreza = random.randint(12, 14)
        constituicao = random.randint(10, 12)
        inteligencia = random.randint(16, 20)
        sabedoria = random.randint(12, 14)
        carisma = random.randint(8, 12)
        mana = 15 + (nivel * 3)
    elif classe == "Assassino":
        vida = 8 + (nivel * 1)
        forca = random.randint(12, 14)
        destreza = random.randint(16, 20)
        constituicao = random.randint(10, 12)
        inteligencia = random.randint(12, 14)
        sabedoria = random.randint(12, 14)
        carisma = random.randint(12, 14)
        mana = 0
    elif classe == "Clérigo":
        vida = 10 + (nivel * 2)
        forca = random.randint(12, 14)
        destreza = random.randint(10, 12)
        constituicao = random.randint(12, 14)
        inteligencia = random.randint(10, 12)
        sabedoria = random.randint(16, 20)
        carisma = random.randint(14, 16)
        mana = 12 + (nivel * 2)
    else:  # Outras classes
        vida = 10 + (nivel * 1)
        forca = random.randint(12, 16)
        destreza = random.randint(12, 16)
        constituicao = random.randint(12, 14)
        inteligencia = random.randint(10, 14)
        sabedoria = random.randint(12, 14)
        carisma = random.randint(10, 14)
        mana = 8 + (nivel * 1)
    
    personagem = {
        "nome": nome,
        "descricao": f"Um(a) {classe.lower()} {raca.lower()} de nível {nivel}",
        "classe": classe,
        "raca": raca,
        "nivel": nivel,
        "experiencia": exp,
        "vida": vida,
        "mana": mana,
        "forca": forca,
        "destreza": destreza,
        "constituicao": constituicao,
        "inteligencia": inteligencia,
        "sabedoria": sabedoria,
        "carisma": carisma,
        "status": random.choice(status),
        "data_criacao": datetime.now().isoformat(),
        "ultima_atualizacao": datetime.now().isoformat()
    }
    
    personagens_data.append({
        "_index": "rpg_personagens",
        "_id": str(i),
        "_source": personagem
    })

print(f"✅ {len(personagens_data)} personagens gerados")

# ============================================================
# INSERIR DADOS
# ============================================================
print("\n📤 Inserindo dados no Elasticsearch...")

try:
    success, failed = helpers.bulk(es, personagens_data, stats_only=True)
    print(f"✅ {success} personagens inseridos com sucesso")
    
    if failed > 0:
        print(f"⚠️  {failed} personagens falharam")
        
except Exception as e:
    print(f"❌ Erro ao inserir dados: {e}")
    sys.exit(1)

# ============================================================
# REFRESH INDEX
# ============================================================
print("\n🔄 Atualizando índice...")
try:
    es.indices.refresh(index="rpg_personagens")
    print("✅ Índice atualizado")
except Exception as e:
    print(f"⚠️  Aviso ao atualizar: {e}")

# ============================================================
# VERIFICAR DADOS
# ============================================================
print("\n📊 Verificando dados inseridos...")

try:
    count_result = es.count(index="rpg_personagens")
    count = count_result['count']
    print(f"✅ Total de personagens: {count}")
    
    search_result = es.search(
        index="rpg_personagens",
        body={"query": {"match_all": {}}, "size": 5}
    )
    
    print("\n📄 Exemplos de personagens inseridos:")
    for hit in search_result['hits']['hits']:
        src = hit['_source']
        print(f"   ID {hit['_id']}: {src['nome']} ({src['classe']}, Nível {src['nivel']}, {src['status']})")
    
except Exception as e:
    print(f"❌ Erro ao verificar: {e}")

print("\n" + "=" * 60)
print("🎉 População de personagens concluída!")
print("=" * 60)
