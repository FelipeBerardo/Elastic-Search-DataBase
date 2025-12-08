# app_rpg_search.py - API Corrigida
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch

app = Flask(__name__)
es = Elasticsearch("http://localhost:9200")

# Verificar conexão
if not es.ping():
    print("❌ Erro: Elasticsearch não está rodando!")
    exit()

print("✅ Conectado ao Elasticsearch")

# ============================================================
# ROTA RAIZ
# ============================================================
@app.route('/')
def home():
    return jsonify({
        'api': 'RPG Search',
        'rotas_disponiveis': [
            '/buscar?q=espada',
            '/filtrar?tipo=Arma&raridade=Lendário',
            '/autocomplete?q=esp',
            '/similares/<item_id>',
            '/dashboard'
        ],
        'exemplos': {
            'buscar': 'curl "http://localhost:5000/buscar?q=espada"',
            'filtrar_get': 'curl "http://localhost:5000/filtrar?tipo=Arma"',
            'filtrar_post': 'curl -X POST http://localhost:5000/filtrar -H "Content-Type: application/json" -d \'{"tipo":"Arma"}\'',
            'autocomplete': 'curl "http://localhost:5000/autocomplete?q=esp"',
            'similares': 'curl "http://localhost:5000/similares/1"',
            'dashboard': 'curl "http://localhost:5000/dashboard"'
        },
        'status': 'ok'
    })

# ============================================================
# 1. BUSCA FULL-TEXT
# ============================================================
@app.route('/buscar', methods=['GET'])
def buscar_itens():
    """Busca full-text de itens"""
    termo = request.args.get('q', '')
    
    # Validar parâmetro
    if not termo:
        return jsonify({
            'error': 'Parâmetro "q" é obrigatório',
            'exemplo': '/buscar?q=espada'
        }), 400
    
    try:
        query = {
            "query": {
                "multi_match": {
                    "query": termo,
                    "fields": ["nome^3", "descricao^2", "tags"],
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            },
            "highlight": {
                "fields": {
                    "nome": {},
                    "descricao": {}
                }
            },
            "size": 20
        }
        
        resp = es.search(index="rpg_itens", body=query)
        
        # Formatar resposta
        resultados = []
        for hit in resp['hits']['hits']:
            item = {
                'id': hit['_id'],
                'score': hit['_score'],
                'nome': hit['_source']['nome'],
                'tipo': hit['_source']['tipo'],
                'raridade': hit['_source']['raridade'],
                'valor': hit['_source']['valor'],
                'descricao': hit['_source']['descricao']
            }
            
            # Adicionar highlights se existirem
            if 'highlight' in hit:
                item['highlights'] = hit['highlight']
            
            resultados.append(item)
        
        return jsonify({
            'total': resp['hits']['total']['value'],
            'query': termo,
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 2. FILTROS COMBINADOS (GET e POST)
# ============================================================
@app.route('/filtrar', methods=['GET', 'POST'])
def filtrar_itens():
    """Filtrar itens por tipo, raridade, valor, etc."""
    
    # Aceitar tanto GET quanto POST
    if request.method == 'POST':
        filtros = request.json or {}
    else:
        # GET: pegar parâmetros da URL
        filtros = {
            'tipo': request.args.get('tipo'),
            'raridade': request.args.get('raridade'),
            'valor_min': request.args.get('valor_min', type=int),
            'valor_max': request.args.get('valor_max', type=int),
            'nivel_min': request.args.get('nivel_min', type=int),
            'nivel_max': request.args.get('nivel_max', type=int)
        }
        # Remover None
        filtros = {k: v for k, v in filtros.items() if v is not None}
    
    if not filtros:
        return jsonify({
            'error': 'Nenhum filtro fornecido',
            'filtros_disponiveis': ['tipo', 'raridade', 'valor_min', 'valor_max', 'nivel_min', 'nivel_max'],
            'exemplo_get': '/filtrar?tipo=Arma&raridade=Lendário',
            'exemplo_post': 'POST /filtrar com JSON {"tipo":"Arma","valor_min":1000}'
        }), 400
    
    try:
        # Construir query
        filters = []
        
        if 'tipo' in filtros:
            filters.append({"term": {"tipo": filtros['tipo']}})
        
        if 'raridade' in filtros:
            filters.append({"term": {"raridade": filtros['raridade']}})
        
        # Range de valor
        if 'valor_min' in filtros or 'valor_max' in filtros:
            range_query = {}
            if 'valor_min' in filtros:
                range_query['gte'] = filtros['valor_min']
            if 'valor_max' in filtros:
                range_query['lte'] = filtros['valor_max']
            filters.append({"range": {"valor": range_query}})
        
        # Range de nível
        if 'nivel_min' in filtros or 'nivel_max' in filtros:
            range_query = {}
            if 'nivel_min' in filtros:
                range_query['gte'] = filtros['nivel_min']
            if 'nivel_max' in filtros:
                range_query['lte'] = filtros['nivel_max']
            filters.append({"range": {"nivel_requerido": range_query}})
        
        query = {
            "query": {
                "bool": {
                    "filter": filters
                }
            },
            "sort": [{"valor": "desc"}],
            "size": 50
        }
        
        resp = es.search(index="rpg_itens", body=query)
        
        # Formatar resposta
        resultados = []
        for hit in resp['hits']['hits']:
            resultados.append({
                'id': hit['_id'],
                'nome': hit['_source']['nome'],
                'tipo': hit['_source']['tipo'],
                'raridade': hit['_source']['raridade'],
                'valor': hit['_source']['valor'],
                'nivel_requerido': hit['_source'].get('nivel_requerido', 0),
                'peso': hit['_source'].get('peso', 0)
            })
        
        return jsonify({
            'total': resp['hits']['total']['value'],
            'filtros_aplicados': filtros,
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 3. AUTOCOMPLETE
# ============================================================
@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    """Sugestões de autocomplete"""
    prefix = request.args.get('q', '')
    
    if not prefix or len(prefix) < 2:
        return jsonify({
            'error': 'Parâmetro "q" deve ter pelo menos 2 caracteres',
            'exemplo': '/autocomplete?q=esp'
        }), 400
    
    try:
        # Busca com prefix
        query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase_prefix": {
                                "nome": {
                                    "query": prefix,
                                    "max_expansions": 10
                                }
                            }
                        },
                        {
                            "wildcard": {
                                "nome.keyword": {
                                    "value": f"*{prefix}*",
                                    "case_insensitive": True
                                }
                            }
                        }
                    ]
                }
            },
            "_source": ["nome", "tipo", "raridade"],
            "size": 10
        }
        
        resp = es.search(index="rpg_itens", body=query)
        
        # Extrair sugestões únicas
        sugestoes = []
        nomes_vistos = set()
        
        for hit in resp['hits']['hits']:
            nome = hit['_source']['nome']
            if nome not in nomes_vistos:
                nomes_vistos.add(nome)
                sugestoes.append({
                    'nome': nome,
                    'tipo': hit['_source']['tipo'],
                    'raridade': hit['_source']['raridade']
                })
        
        return jsonify({
            'query': prefix,
            'total': len(sugestoes),
            'sugestoes': sugestoes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 4. ITENS SIMILARES
# ============================================================
@app.route('/similares/<item_id>', methods=['GET'])
def itens_similares(item_id):
    """Encontrar itens similares usando More Like This"""
    try:
        # Primeiro verificar se item existe
        try:
            item = es.get(index="rpg_itens", id=item_id)
        except:
            return jsonify({'error': f'Item {item_id} não encontrado'}), 404
        
        # More Like This query
        query = {
            "query": {
                "more_like_this": {
                    "fields": ["nome", "descricao", "tags", "tipo"],
                    "like": [{"_index": "rpg_itens", "_id": item_id}],
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                    "min_doc_freq": 1
                }
            },
            "size": 10
        }
        
        resp = es.search(index="rpg_itens", body=query)
        
        # Formatar resposta
        resultados = []
        for hit in resp['hits']['hits']:
            resultados.append({
                'id': hit['_id'],
                'score': hit['_score'],
                'nome': hit['_source']['nome'],
                'tipo': hit['_source']['tipo'],
                'raridade': hit['_source']['raridade'],
                'valor': hit['_source']['valor']
            })
        
        return jsonify({
            'item_original': {
                'id': item_id,
                'nome': item['_source']['nome'],
                'tipo': item['_source']['tipo']
            },
            'total_similares': resp['hits']['total']['value'],
            'similares': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 5. DASHBOARD ANALÍTICO (MELHORADO)
# ============================================================
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Dashboard com estatísticas e agregações"""
    try:
        query = {
            "size": 0,
            "aggs": {
                "por_tipo": {
                    "terms": {
                        "field": "tipo",
                        "size": 10
                    }
                },
                "por_raridade": {
                    "terms": {
                        "field": "raridade",
                        "size": 10
                    }
                },
                "distribuicao_valor": {
                    "histogram": {
                        "field": "valor",
                        "interval": 10000,  # Intervalos de 10k
                        "min_doc_count": 1  # Só mostrar buckets com dados
                    }
                },
                "ranges_valor": {
                    "range": {
                        "field": "valor",
                        "ranges": [
                            {"to": 100, "key": "0-100 (Muito Barato)"},
                            {"from": 100, "to": 1000, "key": "100-1000 (Barato)"},
                            {"from": 1000, "to": 10000, "key": "1k-10k (Médio)"},
                            {"from": 10000, "to": 100000, "key": "10k-100k (Caro)"},
                            {"from": 100000, "key": "100k+ (Muito Caro)"}
                        ]
                    }
                },
                "estatisticas_valor": {
                    "stats": {"field": "valor"}
                },
                "estatisticas_nivel": {
                    "stats": {"field": "nivel_requerido"}
                },
                "top_itens_caros": {
                    "top_hits": {
                        "size": 5,
                        "sort": [{"valor": "desc"}],
                        "_source": ["nome", "tipo", "raridade", "valor"]
                    }
                }
            }
        }
        
        resp = es.search(index="rpg_itens", body=query)
        aggs = resp['aggregations']
        
        # Formatar resposta de forma mais legível
        dashboard_data = {
            'total_itens': resp['hits']['total']['value'],
            
            'por_tipo': [
                {'tipo': b['key'], 'quantidade': b['doc_count']}
                for b in aggs['por_tipo']['buckets']
            ],
            
            'por_raridade': [
                {'raridade': b['key'], 'quantidade': b['doc_count']}
                for b in aggs['por_raridade']['buckets']
            ],
            
            'ranges_valor': [
                {'faixa': b['key'], 'quantidade': b['doc_count']}
                for b in aggs['ranges_valor']['buckets']
            ],
            
            'estatisticas_valor': {
                'minimo': aggs['estatisticas_valor']['min'],
                'maximo': aggs['estatisticas_valor']['max'],
                'media': round(aggs['estatisticas_valor']['avg'], 2),
                'soma_total': aggs['estatisticas_valor']['sum']
            },
            
            'estatisticas_nivel': {
                'minimo': aggs['estatisticas_nivel']['min'],
                'maximo': aggs['estatisticas_nivel']['max'],
                'media': round(aggs['estatisticas_nivel']['avg'], 2)
            },
            
            'top_5_mais_caros': [
                hit['_source'] for hit in aggs['top_itens_caros']['hits']['hits']
            ],
            
            # Só primeiros 20 buckets do histograma
            'distribuicao_valor_histograma': [
                {'valor_min': b['key'], 'quantidade': b['doc_count']}
                for b in aggs['distribuicao_valor']['buckets'][:20]
            ]
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 6. BUSCA AVANÇADA (BÔNUS)
# ============================================================
@app.route('/busca-avancada', methods=['POST'])
def busca_avancada():
    """Busca com múltiplos critérios"""
    data = request.json or {}
    
    must = []
    filters = []
    should = []
    
    # Texto livre
    if 'texto' in data:
        must.append({
            "multi_match": {
                "query": data['texto'],
                "fields": ["nome^3", "descricao"],
                "fuzziness": "AUTO"
            }
        })
    
    # Filtros exatos
    if 'tipo' in data:
        filters.append({"term": {"tipo": data['tipo']}})
    
    if 'raridade' in data:
        filters.append({"term": {"raridade": data['raridade']}})
    
    # Ranges
    if 'valor_min' in data or 'valor_max' in data:
        range_q = {}
        if 'valor_min' in data:
            range_q['gte'] = data['valor_min']
        if 'valor_max' in data:
            range_q['lte'] = data['valor_max']
        filters.append({"range": {"valor": range_q}})
    
    query = {
        "query": {
            "bool": {
                "must": must,
                "filter": filters,
                "should": should
            }
        },
        "size": data.get('size', 20)
    }
    
    resp = es.search(index="rpg_itens", body=query)
    
    return jsonify({
        'total': resp['hits']['total']['value'],
        'resultados': [
            {
                'id': hit['_id'],
                'score': hit['_score'],
                **hit['_source']
            }
            for hit in resp['hits']['hits']
        ]
    })

# ============================================================
# 7. BUSCA PERSONAGENS
# ============================================================
@app.route('/buscar_personagens', methods=['GET'])
def buscar_personagens():
    """Busca de personagens"""
    termo = request.args.get('q', '')
    
    if not termo:
        return jsonify({'error': 'Parâmetro "q" é obrigatório'}), 400
    
    try:
        query = {
            "query": {
                "multi_match": {
                    "query": termo,
                    "fields": ["nome^3", "descricao", "classe", "raca"],
                    "fuzziness": "AUTO"
                }
            },
            "size": 20
        }
        
        resp = es.search(index="rpg_personagens", body=query)
        
        resultados = []
        for hit in resp['hits']['hits']:
            resultados.append({
                'id': hit['_id'],
                'nome': hit['_source']['nome'],
                'classe': hit['_source']['classe'],
                'raca': hit['_source']['raca'],
                'nivel': hit['_source']['nivel'],
                'status': hit['_source']['status'],
                'experiencia': hit['_source'].get('experiencia', 0),
                'vida': hit['_source'].get('vida', 0),
                'forca': hit['_source'].get('forca', 0),
                'destreza': hit['_source'].get('destreza', 0),
                'inteligencia': hit['_source'].get('inteligencia', 0)
            })
        
        return jsonify({
            'total': resp['hits']['total']['value'],
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 8. FILTRAR PERSONAGENS
# ============================================================
@app.route('/filtrar_personagens', methods=['POST'])
def filtrar_personagens():
    """Filtrar personagens"""
    data = request.json or {}
    
    filters = []
    
    if 'classe' in data:
        filters.append({"term": {"classe": data['classe']}})
    
    if 'raca' in data:
        filters.append({"term": {"raca": data['raca']}})
    
    if 'status' in data:
        filters.append({"term": {"status": data['status']}})
    
    if 'nivel_min' in data or 'nivel_max' in data:
        range_query = {}
        if 'nivel_min' in data:
            range_query['gte'] = data['nivel_min']
        if 'nivel_max' in data:
            range_query['lte'] = data['nivel_max']
        filters.append({"range": {"nivel": range_query}})
    
    query = {
        "query": {"bool": {"filter": filters} if filters else {"match_all": {}}},
        "sort": [{"nivel": "desc"}],
        "size": 100
    }
    
    try:
        resp = es.search(index="rpg_personagens", body=query)
        
        resultados = []
        for hit in resp['hits']['hits']:
            resultados.append({
                'nome': hit['_source']['nome'],
                'classe': hit['_source']['classe'],
                'raca': hit['_source']['raca'],
                'nivel': hit['_source']['nivel'],
                'status': hit['_source']['status'],
                'experiencia': hit['_source'].get('experiencia', 0)
            })
        
        return jsonify({
            'total': resp['hits']['total']['value'],
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 9. DASHBOARD PERSONAGENS
# ============================================================
@app.route('/dashboard_personagens', methods=['GET'])
def dashboard_personagens():
    """Dashboard de personagens"""
    try:
        query = {
            "size": 0,
            "aggs": {
                "por_classe": {"terms": {"field": "classe", "size": 20}},
                "por_raca": {"terms": {"field": "raca", "size": 20}},
                "por_status": {"terms": {"field": "status", "size": 10}},
                "nivel_stats": {"stats": {"field": "nivel"}},
                "exp_stats": {"stats": {"field": "experiencia"}},
                "total_ativos": {
                    "filter": {"term": {"status": "Ativo"}}
                }
            }
        }
        
        resp = es.search(index="rpg_personagens", body=query)
        aggs = resp['aggregations']
        
        return jsonify({
            'total_personagens': resp['hits']['total']['value'],
            'nivel_medio': aggs['nivel_stats']['avg'],
            'exp_media': aggs['exp_stats']['avg'],
            'total_ativos': aggs['total_ativos']['doc_count'],
            'por_classe': [{'classe': b['key'], 'quantidade': b['doc_count']} for b in aggs['por_classe']['buckets']],
            'por_raca': [{'raca': b['key'], 'quantidade': b['doc_count']} for b in aggs['por_raca']['buckets']]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 10. TOP PERSONAGENS
# ============================================================
@app.route('/top_personagens', methods=['GET'])
def top_personagens():
    """Top personagens"""
    ordenar_por = request.args.get('ordenar_por', 'nivel').lower()
    
    # Campos válidos para ordenação
    campos_validos = ['nivel', 'experiencia', 'vida', 'forca']
    if ordenar_por not in campos_validos:
        ordenar_por = 'nivel'
    
    try:
        query = {
            "query": {"match_all": {}},
            "sort": [{ordenar_por: "desc"}],
            "size": 10
        }
        
        resp = es.search(index="rpg_personagens", body=query)
        
        personagens = []
        for hit in resp['hits']['hits']:
            personagens.append({
                'nome': hit['_source']['nome'],
                'classe': hit['_source']['classe'],
                'nivel': hit['_source']['nivel'],
                'experiencia': hit['_source'].get('experiencia', 0),
                'vida': hit['_source'].get('vida', 0)
            })
        
        return jsonify({'personagens': personagens})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 11. BUSCA MISSÕES
# ============================================================
@app.route('/buscar_missoes', methods=['GET'])
def buscar_missoes():
    """Busca de missões"""
    termo = request.args.get('q', '')
    
    if not termo:
        return jsonify({'error': 'Parâmetro "q" é obrigatório'}), 400
    
    try:
        query = {
            "query": {
                "multi_match": {
                    "query": termo,
                    "fields": ["titulo^3", "descricao", "objetivo", "tipo"],
                    "fuzziness": "AUTO"
                }
            },
            "size": 20
        }
        
        resp = es.search(index="rpg_missoes", body=query)
        
        resultados = []
        for hit in resp['hits']['hits']:
            resultados.append({
                'id': hit['_id'],
                'titulo': hit['_source']['titulo'],
                'dificuldade': hit['_source']['dificuldade'],
                'tipo': hit['_source']['tipo'],
                'recompensa_ouro': hit['_source']['recompensa_ouro'],
                'recompensa_experiencia': hit['_source']['recompensa_experiencia'],
                'nivel_minimo': hit['_source']['nivel_minimo'],
                'nivel_maximo': hit['_source']['nivel_maximo'],
                'localizacao': hit['_source']['localizacao'],
                'objetivo': hit['_source']['objetivo'],
                'taxa_conclusao_pct': hit['_source'].get('taxa_conclusao_pct', 0)
            })
        
        return jsonify({
            'total': resp['hits']['total']['value'],
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 12. FILTRAR MISSÕES
# ============================================================
@app.route('/filtrar_missoes', methods=['POST'])
def filtrar_missoes():
    """Filtrar missões"""
    data = request.json or {}
    
    filters = []
    
    if 'dificuldade' in data:
        filters.append({"term": {"dificuldade": data['dificuldade']}})
    
    if 'tipo' in data:
        filters.append({"term": {"tipo": data['tipo']}})
    
    if 'nivel_min' in data or 'nivel_max' in data:
        range_query = {}
        if 'nivel_min' in data:
            range_query['gte'] = data['nivel_min']
        if 'nivel_max' in data:
            range_query['lte'] = data['nivel_max']
        filters.append({"range": {"nivel_minimo": range_query}})
    
    if 'ouro_min' in data or 'ouro_max' in data:
        range_query = {}
        if 'ouro_min' in data:
            range_query['gte'] = data['ouro_min']
        if 'ouro_max' in data:
            range_query['lte'] = data['ouro_max']
        filters.append({"range": {"recompensa_ouro": range_query}})
    
    query = {
        "query": {"bool": {"filter": filters} if filters else {"match_all": {}}},
        "sort": [{"recompensa_ouro": "desc"}],
        "size": 100
    }
    
    try:
        resp = es.search(index="rpg_missoes", body=query)
        
        resultados = []
        for hit in resp['hits']['hits']:
            resultados.append({
                'titulo': hit['_source']['titulo'],
                'dificuldade': hit['_source']['dificuldade'],
                'tipo': hit['_source']['tipo'],
                'recompensa_ouro': hit['_source']['recompensa_ouro'],
                'nivel_minimo': hit['_source']['nivel_minimo'],
                'nivel_maximo': hit['_source']['nivel_maximo']
            })
        
        return jsonify({
            'total': resp['hits']['total']['value'],
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 13. DASHBOARD MISSÕES
# ============================================================
@app.route('/dashboard_missoes', methods=['GET'])
def dashboard_missoes():
    """Dashboard de missões"""
    try:
        query = {
            "size": 0,
            "aggs": {
                "por_dificuldade": {"terms": {"field": "dificuldade", "size": 10}},
                "por_tipo": {"terms": {"field": "tipo", "size": 20}},
                "ouro_stats": {"stats": {"field": "recompensa_ouro"}},
                "xp_stats": {"stats": {"field": "recompensa_experiencia"}},
                "taxa_media": {"avg": {"field": "taxa_conclusao_pct"}}
            }
        }
        
        resp = es.search(index="rpg_missoes", body=query)
        aggs = resp['aggregations']
        
        return jsonify({
            'total_missoes': resp['hits']['total']['value'],
            'ouro_medio': aggs['ouro_stats']['avg'],
            'xp_medio': aggs['xp_stats']['avg'],
            'taxa_media': aggs['taxa_media']['value'],
            'por_dificuldade': [{'dificuldade': b['key'], 'quantidade': b['doc_count']} for b in aggs['por_dificuldade']['buckets']],
            'por_tipo': [{'tipo': b['key'], 'quantidade': b['doc_count']} for b in aggs['por_tipo']['buckets']]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# 14. MISSÕES POR DIFICULDADE
# ============================================================
@app.route('/missoes_dificuldade', methods=['GET'])
def missoes_dificuldade():
    """Missões filtradas por dificuldade"""
    dificuldade = request.args.get('dificuldade', '')
    
    try:
        query = {
            "query": {"term": {"dificuldade": dificuldade}},
            "sort": [{"recompensa_ouro": "desc"}],
            "size": 50,
            "aggs": {
                "ouro_media": {"avg": {"field": "recompensa_ouro"}},
                "taxa_media": {"avg": {"field": "taxa_conclusao_pct"}}
            }
        }
        
        resp = es.search(index="rpg_missoes", body=query)
        
        missoes = []
        for hit in resp['hits']['hits']:
            missoes.append({
                'titulo': hit['_source']['titulo'],
                'recompensa_ouro': hit['_source']['recompensa_ouro']
            })
        
        return jsonify({
            'missoes': missoes,
            'ouro_medio': resp['aggregations']['ouro_media']['value'],
            'taxa_media': resp['aggregations']['taxa_media']['value']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# EXECUTAR APP
# ============================================================
if __name__ == '__main__':
    print("\n🚀 API RPG Search iniciada!")
    print("📖 Documentação: http://localhost:5000")
    print("\n🔍 Exemplos de uso:")
    print("  curl 'http://localhost:5000/buscar?q=espada'")
    print("  curl 'http://localhost:5000/filtrar?tipo=Arma&raridade=Lendário'")
    print("  curl 'http://localhost:5000/autocomplete?q=esp'")
    print("  curl 'http://localhost:5000/dashboard'")
    print("\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)