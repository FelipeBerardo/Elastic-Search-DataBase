#!/usr/bin/env python3
# frontend_web_rpg.py - Frontend Web Streamlit para RPG Search

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="RPG Search - Web Frontend",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CONFIGURAÇÃO DA API
# ============================================================
API_URL = "http://localhost:5000"

# Verificar conexão com API
@st.cache_resource
def verificar_api():
    try:
        resp = requests.get(f"{API_URL}/", timeout=5)
        return resp.status_code == 200
    except:
        return False

# ============================================================
# FUNÇÕES DE REQUISIÇÃO À API
# ============================================================

def buscar_itens(termo):
    """Realizar busca full-text"""
    try:
        resp = requests.get(f"{API_URL}/buscar", params={"q": termo}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"Erro: {resp.json().get('error', 'Erro desconhecido')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return None

def filtrar_itens(filtros):
    """Filtrar itens com critérios"""
    try:
        resp = requests.post(f"{API_URL}/filtrar", json=filtros, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"Erro: {resp.json().get('error', 'Erro desconhecido')}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return None

def obter_dashboard():
    """Obter dados do dashboard"""
    try:
        resp = requests.get(f"{API_URL}/dashboard", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error("Erro ao carregar dashboard")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return None

def buscar_similares(item_id):
    """Encontrar itens similares"""
    try:
        resp = requests.get(f"{API_URL}/similares/{item_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"Erro: Item não encontrado")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return None

def autocomplete(prefix):
    """Buscar sugestões de autocomplete"""
    try:
        resp = requests.get(f"{API_URL}/autocomplete", params={"q": prefix}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return None
    except:
        return None

def busca_avancada(criterios):
    """Realizar busca avançada"""
    try:
        resp = requests.post(f"{API_URL}/busca-avancada", json=criterios, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"Erro na busca avançada")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erro ao conectar com a API: {e}")
        return None

# ============================================================
# PÁGINA: BUSCA RÁPIDA
# ============================================================

def pagina_busca_rapida():
    st.header("🔍 Busca Rápida")
    st.write("Busque itens pelo nome, descrição ou tags")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        termo = st.text_input(
            "Digite o termo de busca:",
            placeholder="Ex: espada, poção, lendário...",
            label_visibility="collapsed"
        )
    
    with col2:
        buscar = st.button("🔍 Buscar", use_container_width=True)
    
    if buscar and termo:
        with st.spinner("🔍 Buscando..."):
            resultado = buscar_itens(termo)
        
        if resultado:
            total = resultado.get('total', 0)
            st.success(f"✅ Encontrados {total} itens para '{termo}'")
            
            if total > 0:
                itens = resultado.get('resultados', [])
                
                # Criar DataFrame para exibição
                df_data = []
                for item in itens:
                    df_data.append({
                        'ID': item['id'],
                        'Nome': item['nome'],
                        'Tipo': item['tipo'],
                        'Raridade': item['raridade'],
                        'Valor (PO)': item['valor'],
                        'Score': f"{item['score']:.2f}"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Exibir detalhes dos itens
                st.subheader("📋 Detalhes dos Itens")
                
                for item in itens:
                    with st.expander(f"📦 {item['nome']} ({item['raridade']})"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Tipo", item['tipo'])
                            st.metric("Raridade", item['raridade'])
                        
                        with col2:
                            st.metric("Valor (PO)", f"{item['valor']:,}")
                            st.metric("Score", f"{item['score']:.2f}")
                        
                        with col3:
                            st.metric("ID", item['id'])
                        
                        st.write(f"**Descrição:** {item['descricao']}")
                        
                        # Botão para ver similares
                        if st.button(f"🎁 Ver similares", key=f"similar_{item['id']}"):
                            st.session_state.item_id_similar = item['id']
            else:
                st.info("Nenhum item encontrado.")

# ============================================================
# PÁGINA: FILTROS
# ============================================================

def pagina_filtros():
    st.header("🎯 Filtros Avançados")
    st.write("Combine múltiplos filtros para encontrar itens específicos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipos = st.multiselect(
            "🛡️ Tipos",
            options=["Arma", "Armadura", "Acessório", "Consumível", "Livro", "Componente Arcano"],
            default=[]
        )
    
    with col2:
        raridades = st.multiselect(
            "⭐ Raridades",
            options=["Comum", "Incomum", "Raro", "Muito Raro", "Lendário", "Artefato"],
            default=[]
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        valor_min = st.number_input(
            "💰 Valor Mínimo (PO)",
            min_value=0,
            value=0,
            step=100
        )
    
    with col2:
        valor_max = st.number_input(
            "💰 Valor Máximo (PO)",
            min_value=0,
            value=100000,
            step=100
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_min = st.number_input(
            "📊 Nível Mínimo",
            min_value=1,
            value=1,
            step=1
        )
    
    with col2:
        nivel_max = st.number_input(
            "📊 Nível Máximo",
            min_value=1,
            value=20,
            step=1
        )
    
    if st.button("🔍 Aplicar Filtros", use_container_width=True, type="primary"):
        # Construir filtros
        filtros = {}
        
        if tipos:
            filtros['tipo'] = tipos[0]  # A API aceita apenas um tipo por vez
        
        if raridades:
            filtros['raridade'] = raridades[0]  # A API aceita apenas uma raridade por vez
        
        if valor_min > 0:
            filtros['valor_min'] = valor_min
        
        if valor_max > 0:
            filtros['valor_max'] = valor_max
        
        if nivel_min > 0:
            filtros['nivel_min'] = nivel_min
        
        if nivel_max > 0:
            filtros['nivel_max'] = nivel_max
        
        if filtros:
            with st.spinner("🔍 Aplicando filtros..."):
                resultado = filtrar_itens(filtros)
            
            if resultado:
                total = resultado.get('total', 0)
                st.success(f"✅ Encontrados {total} itens")
                
                if total > 0:
                    itens = resultado.get('resultados', [])
                    
                    # Criar DataFrame
                    df_data = []
                    for item in itens:
                        df_data.append({
                            'ID': item['id'],
                            'Nome': item['nome'],
                            'Tipo': item['tipo'],
                            'Raridade': item['raridade'],
                            'Valor (PO)': item['valor'],
                            'Nível': item.get('nivel_requerido', 0),
                            'Peso': item.get('peso', 0)
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Gráfico de distribuição
                    st.subheader("📊 Análise dos Resultados")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(
                            df,
                            x='Tipo',
                            title="Quantidade por Tipo",
                            labels={'Tipo': 'Tipo de Item', 'count': 'Quantidade'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        fig = px.pie(
                            df,
                            names='Raridade',
                            title="Distribuição por Raridade"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum item encontrado com esses filtros.")
        else:
            st.warning("⚠️ Por favor, aplique pelo menos um filtro.")

# ============================================================
# PÁGINA: DASHBOARD
# ============================================================

def pagina_dashboard():
    st.header("📊 Dashboard Analítico")
    st.write("Visualize estatísticas e análises do banco de dados")
    
    with st.spinner("📊 Carregando dashboard..."):
        dados = obter_dashboard()
    
    if dados:
        # Métricas principais
        st.subheader("📈 Métricas Principais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📦 Total de Itens",
                f"{dados.get('total_itens', 0):,}",
                delta=None
            )
        
        with col2:
            valor_total = dados['estatisticas_valor']['soma_total']
            st.metric(
                "💰 Valor Total (PO)",
                f"{valor_total:,.0f}",
                delta=None
            )
        
        with col3:
            valor_medio = dados['estatisticas_valor']['media']
            st.metric(
                "💵 Valor Médio (PO)",
                f"{valor_medio:,.0f}",
                delta=None
            )
        
        with col4:
            nivel_medio = dados['estatisticas_nivel']['media']
            st.metric(
                "📊 Nível Médio",
                f"{nivel_medio:.1f}",
                delta=None
            )
        
        # Gráficos de análise
        st.subheader("📊 Análises")
        
        col1, col2 = st.columns(2)
        
        # Gráfico: Por Tipo
        with col1:
            df_tipo = pd.DataFrame(dados['por_tipo'])
            fig = px.bar(
                df_tipo,
                x='tipo',
                y='quantidade',
                title="Quantidade de Itens por Tipo",
                labels={'tipo': 'Tipo', 'quantidade': 'Quantidade'},
                color='quantidade'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico: Por Raridade
        with col2:
            df_raridade = pd.DataFrame(dados['por_raridade'])
            fig = px.pie(
                df_raridade,
                names='raridade',
                values='quantidade',
                title="Distribuição por Raridade"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico: Faixa de Valor
        col1, col2 = st.columns(2)
        
        with col1:
            df_ranges = pd.DataFrame(dados['ranges_valor'])
            fig = px.bar(
                df_ranges,
                x='faixa',
                y='quantidade',
                title="Distribuição por Faixa de Valor",
                labels={'faixa': 'Faixa de Valor', 'quantidade': 'Quantidade'},
                color='quantidade'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Histograma de Valor
        with col2:
            df_hist = pd.DataFrame(dados['distribuicao_valor_histograma'])
            if not df_hist.empty:
                fig = px.bar(
                    df_hist,
                    x='valor_min',
                    y='quantidade',
                    title="Histograma de Valores",
                    labels={'valor_min': 'Faixa de Valor', 'quantidade': 'Quantidade'},
                    color='quantidade'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Top 5 mais caros
        st.subheader("🏆 Top 5 Itens Mais Valiosos")
        
        df_top = pd.DataFrame(dados['top_5_mais_caros'])
        
        if not df_top.empty:
            df_top_display = df_top[['nome', 'tipo', 'raridade', 'valor']].copy()
            df_top_display.columns = ['Nome', 'Tipo', 'Raridade', 'Valor (PO)']
            df_top_display['Valor (PO)'] = df_top_display['Valor (PO)'].apply(lambda x: f"{x:,}")
            
            st.dataframe(df_top_display, use_container_width=True, hide_index=True)
        
        # Estatísticas de Valor
        st.subheader("💰 Estatísticas de Valor")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        stats = dados['estatisticas_valor']
        
        with col1:
            st.metric("Mínimo", f"{stats['minimo']:,} PO")
        
        with col2:
            st.metric("Máximo", f"{stats['maximo']:,} PO")
        
        with col3:
            st.metric("Média", f"{stats['media']:,} PO")
        
        with col4:
            st.metric("Soma", f"{stats['soma_total']:,} PO")
        
        with col5:
            st.metric("Total de Itens", f"{dados['total_itens']}")

# ============================================================
# PÁGINA: ITENS SIMILARES
# ============================================================

def pagina_similares():
    st.header("🎁 Itens Similares")
    st.write("Encontre itens similares a um item específico")
    
    item_id = st.text_input(
        "Digite o ID do item:",
        placeholder="Ex: 1, 2, 3...",
        label_visibility="collapsed"
    )
    
    if st.button("🔍 Buscar Similares", use_container_width=True, type="primary"):
        if item_id:
            with st.spinner("🔍 Buscando itens similares..."):
                resultado = buscar_similares(item_id)
            
            if resultado:
                item_original = resultado.get('item_original', {})
                similares = resultado.get('similares', [])
                total = resultado.get('total_similares', 0)
                
                st.subheader(f"📌 Item Original: {item_original.get('nome', 'Desconhecido')}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("ID", item_original.get('id', '-'))
                
                with col2:
                    st.metric("Tipo", item_original.get('tipo', '-'))
                
                with col3:
                    pass
                
                st.divider()
                
                st.subheader(f"🎁 Itens Similares ({total})")
                
                if total > 0:
                    df_data = []
                    for item in similares:
                        df_data.append({
                            'ID': item['id'],
                            'Nome': item['nome'],
                            'Tipo': item['tipo'],
                            'Raridade': item['raridade'],
                            'Valor (PO)': item['valor'],
                            'Score': f"{item['score']:.2f}"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Gráfico de comparação
                    fig = px.bar(
                        df,
                        x='Nome',
                        y='Valor (PO)',
                        title="Comparação de Valores",
                        color='Raridade'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum item similar encontrado.")
        else:
            st.warning("⚠️ Por favor, digite um ID de item.")

# ============================================================
# PÁGINA: BUSCA AVANÇADA
# ============================================================

def pagina_busca_avancada():
    st.header("🔎 Busca Avançada")
    st.write("Combine texto livre com filtros específicos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        texto = st.text_input(
            "🔤 Texto (nome, descrição, tags)",
            placeholder="Ex: espada, poção..."
        )
    
    with col2:
        tamanho = st.number_input(
            "📊 Número de resultados",
            min_value=1,
            max_value=100,
            value=20
        )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo = st.selectbox(
            "🛡️ Tipo (opcional)",
            options=["", "Arma", "Armadura", "Acessório", "Consumível", "Livro", "Componente Arcano"]
        )
    
    with col2:
        raridade = st.selectbox(
            "⭐ Raridade (opcional)",
            options=["", "Comum", "Incomum", "Raro", "Muito Raro", "Lendário", "Artefato"]
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        valor_min = st.number_input(
            "💰 Valor Mínimo",
            min_value=0,
            value=0,
            step=100
        )
    
    with col2:
        valor_max = st.number_input(
            "💰 Valor Máximo",
            min_value=0,
            value=100000,
            step=100
        )
    
    if st.button("🔍 Buscar", use_container_width=True, type="primary"):
        criterios = {'size': tamanho}
        
        if texto:
            criterios['texto'] = texto
        
        if tipo:
            criterios['tipo'] = tipo
        
        if raridade:
            criterios['raridade'] = raridade
        
        if valor_min > 0:
            criterios['valor_min'] = valor_min
        
        if valor_max > 0:
            criterios['valor_max'] = valor_max
        
        with st.spinner("🔍 Buscando..."):
            resultado = busca_avancada(criterios)
        
        if resultado:
            total = resultado.get('total', 0)
            st.success(f"✅ Encontrados {total} itens")
            
            if total > 0:
                itens = resultado.get('resultados', [])
                
                # Criar DataFrame
                df_data = []
                for item in itens:
                    df_data.append({
                        'ID': item.get('id', item.get('_id', '-')),
                        'Nome': item.get('nome', '-'),
                        'Tipo': item.get('tipo', '-'),
                        'Raridade': item.get('raridade', '-'),
                        'Valor (PO)': item.get('valor', 0),
                        'Score': f"{item.get('score', 0):.2f}"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        df,
                        x='Tipo',
                        title="Quantidade por Tipo",
                        color='Tipo'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.scatter(
                        df,
                        x='Valor (PO)',
                        y='Score',
                        color='Raridade',
                        hover_name='Nome',
                        title="Valor vs Score"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum item encontrado.")
        else:
            st.error("Erro ao realizar busca.")

# ============================================================
# PÁGINA: SOBRE
# ============================================================

def pagina_sobre():
    st.header("ℹ️ Sobre RPG Search")
    
    st.markdown("""
    ## 🎮 RPG Item Search - Frontend Web
    
    Uma aplicação web moderna para buscar e filtrar itens de RPG armazenados no Elasticsearch.
    
    ### ✨ Funcionalidades
    
    - **🔍 Busca Rápida**: Busca full-text em nomes, descrições e tags
    - **🎯 Filtros Avançados**: Combine múltiplos critérios de filtro
    - **📊 Dashboard Analítico**: Visualize estatísticas e análises dos dados
    - **🎁 Itens Similares**: Encontre itens parecidos com um item específico
    - **🔎 Busca Avançada**: Combine texto livre com filtros específicos
    
    ### 🛠️ Tecnologias
    
    - **Frontend**: Streamlit
    - **Backend**: Flask + Elasticsearch
    - **Banco de Dados**: Elasticsearch
    - **Visualização**: Plotly
    
    ### 📊 Dados
    
    O banco de dados contém itens de RPG com as seguintes categorias:
    
    - **Tipos**: Arma, Armadura, Acessório, Consumível, Livro, Componente Arcano
    - **Raridades**: Comum, Incomum, Raro, Muito Raro, Lendário, Artefato
    - **Atributos**: Valor, Peso, Nível Requerido, Descrição, Tags
    
    ### 🚀 Como Usar
    
    1. Certifique-se de que o Elasticsearch está rodando: `docker-compose up -d`
    2. Inicie a API Flask: `python app_rpg_search.py`
    3. Abra esta aplicação web: `streamlit run frontend_web_rpg.py`
    4. Acesse em: `http://localhost:8501`
    
    ### 📝 API Disponível
    
    A API Flask fornece os seguintes endpoints:
    
    - `GET /buscar?q=termo` - Busca full-text
    - `POST /filtrar` - Filtros combinados
    - `GET /autocomplete?q=prefixo` - Sugestões de autocomplete
    - `GET /similares/<id>` - Itens similares
    - `GET /dashboard` - Dados do dashboard
    - `POST /busca-avancada` - Busca com múltiplos critérios
    
    ### 👨‍💻 Desenvolvedor
    
    Aplicação web para gerenciar e buscar itens de RPG no Elasticsearch.
    """)
    
    st.divider()
    
    # Verificar status da API
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if verificar_api():
            st.success("✅ API Flask conectada")
        else:
            st.error("❌ API Flask não disponível")
    
    with col2:
        st.info("📍 Elasticsearch: http://localhost:9200")
    
    with col3:
        st.info("🌐 API Flask: http://localhost:5000")

# ============================================================
# BARRA LATERAL
# ============================================================

st.sidebar.title("⚔️ RPG SEARCH")
st.sidebar.markdown("---")

# Seletor de módulo
modulo = st.sidebar.selectbox(
    "🎮 Módulo",
    options=["Itens", "Personagens", "Missões"]
)

st.sidebar.markdown("---")

# Menu de navegação dinamicamente baseado no módulo
if modulo == "Itens":
    pagina = st.sidebar.radio(
        "📋 Menu",
        options=[
            "🔍 Busca Rápida",
            "🎯 Filtros",
            "📊 Dashboard",
            "🎁 Similares",
            "🔎 Busca Avançada",
            "⚙️ Gerenciar Itens"
        ]
    )
elif modulo == "Personagens":
    pagina = st.sidebar.radio(
        "📋 Menu",
        options=[
            "🔍 Busca Personagens",
            "🎯 Filtrar Personagens",
            "📊 Dashboard Personagens",
            "🏆 Top Personagens",
            "⚙️ Gerenciar Personagens"
        ]
    )
else:  # Missões
    pagina = st.sidebar.radio(
        "📋 Menu",
        options=[
            "🔍 Busca Missões",
            "🎯 Filtrar Missões",
            "📊 Dashboard Missões",
            "🏆 Missões por Dificuldade",
            "⚙️ Gerenciar Missões"
        ]
    )

st.sidebar.markdown("---")

st.sidebar.markdown("---")

# Status da API
st.sidebar.subheader("📊 Status")

if verificar_api():
    st.sidebar.success("✅ Conectado à API")
else:
    st.sidebar.error("❌ API não disponível")
    st.sidebar.info("""
    Certifique-se de executar:
    1. `docker-compose up -d`
    2. `python app_rpg_search.py`
    """)

st.sidebar.markdown("---")

# Dicas rápidas
with st.sidebar.expander("💡 Dicas Rápidas"):
    st.markdown("""
    - Use **Busca Rápida** para procuras simples
    - Combine **Filtros** para resultados precisos
    - Veja **Dashboard** para análises gerais
    - Explore **Itens Similares** por ID
    - Use **Busca Avançada** para critérios complexos
    """)

# ============================================================
# PÁGINA: BUSCA PERSONAGENS
# ============================================================

def pagina_busca_personagens():
    st.header("🔍 Busca de Personagens")
    st.write("Busque personagens por nome, classe ou raça")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        termo = st.text_input(
            "Digite o termo de busca:",
            placeholder="Ex: Aragorn, Mago, Elfo...",
            label_visibility="collapsed"
        )
    
    with col2:
        buscar = st.button("🔍 Buscar", use_container_width=True, key="btn_busca_perso")
    
    if buscar and termo:
        with st.spinner("🔍 Buscando personagens..."):
            try:
                resp = requests.get(
                    f"{API_URL}/buscar_personagens",
                    params={"q": termo},
                    timeout=10
                )
                if resp.status_code == 200:
                    resultado = resp.json()
                else:
                    st.error("Erro na busca")
                    return
            except:
                st.error("Erro ao conectar com a API")
                return
        
        total = resultado.get('total', 0)
        st.success(f"✅ Encontrados {total} personagens para '{termo}'")
        
        if total > 0:
            personagens = resultado.get('resultados', [])
            
            df_data = []
            for p in personagens:
                df_data.append({
                    'ID': p['id'],
                    'Nome': p['nome'],
                    'Classe': p['classe'],
                    'Raça': p['raca'],
                    'Nível': p['nivel'],
                    'Status': p['status']
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.subheader("📋 Detalhes dos Personagens")
            
            for p in personagens:
                with st.expander(f"🎭 {p['nome']} - {p['classe']} ({p['raca']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Classe", p['classe'])
                        st.metric("Raça", p['raca'])
                        st.metric("Nível", p['nivel'])
                    
                    with col2:
                        st.metric("Status", p['status'])
                        st.metric("Experiência", f"{p.get('experiencia', 0):,}")
                        st.metric("Vida", f"{p.get('vida', 0)}")
                    
                    with col3:
                        st.metric("Força", p.get('forca', 0))
                        st.metric("Destreza", p.get('destreza', 0))
                        st.metric("Inteligência", p.get('inteligencia', 0))
        else:
            st.info("Nenhum personagem encontrado.")

# ============================================================
# PÁGINA: FILTRAR PERSONAGENS
# ============================================================

def pagina_filtrar_personagens():
    st.header("🎯 Filtrar Personagens")
    st.write("Filtre personagens por classe, raça e nível")
    
    col1, col2 = st.columns(2)
    
    with col1:
        classes = st.multiselect(
            "🎭 Classes",
            options=["Guerreiro", "Mago", "Assassino", "Paladino", "Ranger", "Bardo", "Druida", "Clérigo"],
            default=[]
        )
    
    with col2:
        racas = st.multiselect(
            "👥 Raças",
            options=["Humano", "Elfo", "Anão", "Gnomo", "Meio-Orc", "Meio-Elfo", "Tiefling", "Dracônico"],
            default=[]
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_min = st.number_input("📊 Nível Mínimo", min_value=1, value=1)
    
    with col2:
        nivel_max = st.number_input("📊 Nível Máximo", min_value=1, value=20)
    
    status = st.multiselect(
        "✨ Status",
        options=["Ativo", "Inativo", "Morto", "Congelado"],
        default=[]
    )
    
    if st.button("🔍 Aplicar Filtros", use_container_width=True, type="primary"):
        filtros = {
            'classe': classes[0] if classes else None,
            'raca': racas[0] if racas else None,
            'nivel_min': nivel_min,
            'nivel_max': nivel_max,
            'status': status[0] if status else None
        }
        filtros = {k: v for k, v in filtros.items() if v is not None}
        
        if filtros:
            with st.spinner("🔍 Filtrando personagens..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/filtrar_personagens",
                        json=filtros,
                        timeout=10
                    )
                    if resp.status_code == 200:
                        resultado = resp.json()
                    else:
                        st.error("Erro na filtragem")
                        return
                except:
                    st.error("Erro ao conectar com a API")
                    return
            
            total = resultado.get('total', 0)
            st.success(f"✅ Encontrados {total} personagens")
            
            if total > 0:
                personagens = resultado.get('resultados', [])
                
                df_data = []
                for p in personagens:
                    df_data.append({
                        'Nome': p['nome'],
                        'Classe': p['classe'],
                        'Raça': p['raca'],
                        'Nível': p['nivel'],
                        'Experiência': p.get('experiencia', 0),
                        'Status': p['status']
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(
                        df,
                        x='Classe',
                        title="Quantidade por Classe"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(
                        df,
                        names='Status',
                        title="Distribuição por Status"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum personagem encontrado.")

# ============================================================
# PÁGINA: DASHBOARD PERSONAGENS
# ============================================================

def pagina_dashboard_personagens():
    st.header("📊 Dashboard de Personagens")
    st.write("Visualize estatísticas dos personagens")
    
    with st.spinner("📊 Carregando dashboard..."):
        try:
            resp = requests.get(f"{API_URL}/dashboard_personagens", timeout=10)
            if resp.status_code == 200:
                dados = resp.json()
            else:
                st.error("Erro ao carregar dashboard")
                return
        except:
            st.error("Erro ao conectar com a API")
            return
    
    if dados:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total de Personagens", f"{dados.get('total_personagens', 0)}")
        
        with col2:
            st.metric("📊 Nível Médio", f"{dados.get('nivel_medio', 0):.1f}")
        
        with col3:
            st.metric("⭐ Experiência Média", f"{dados.get('exp_media', 0):,.0f}")
        
        with col4:
            st.metric("✨ Ativos", f"{dados.get('total_ativos', 0)}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            df_classe = pd.DataFrame(dados.get('por_classe', []))
            if not df_classe.empty:
                fig = px.bar(
                    df_classe,
                    x='classe',
                    y='quantidade',
                    title="Personagens por Classe"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            df_raca = pd.DataFrame(dados.get('por_raca', []))
            if not df_raca.empty:
                fig = px.pie(
                    df_raca,
                    names='raca',
                    values='quantidade',
                    title="Distribuição por Raça"
                )
                st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA: TOP PERSONAGENS
# ============================================================

def pagina_top_personagens():
    st.header("🏆 Top Personagens")
    st.write("Os personagens mais poderosos e experientes")
    
    opcao = st.radio(
        "Ordenar por:",
        options=["Nível", "Experiência", "Vida", "Força"],
        horizontal=True
    )
    
    with st.spinner("🔍 Buscando..."):
        try:
            resp = requests.get(
                f"{API_URL}/top_personagens",
                params={"ordenar_por": opcao.lower()},
                timeout=10
            )
            if resp.status_code == 200:
                resultado = resp.json()
            else:
                st.error("Erro ao carregar")
                return
        except:
            st.error("Erro ao conectar com a API")
            return
    
    personagens = resultado.get('personagens', [])
    
    if personagens:
        df_data = []
        for i, p in enumerate(personagens, 1):
            df_data.append({
                'Ranking': i,
                'Nome': p['nome'],
                'Classe': p['classe'],
                'Nível': p['nivel'],
                'Experiência': p.get('experiencia', 0),
                'Vida': p.get('vida', 0)
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        fig = px.bar(
            df,
            x='Nome',
            y='Nível',
            color='Classe',
            title="Top Personagens"
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA: BUSCA MISSÕES
# ============================================================

def pagina_busca_missoes():
    st.header("🔍 Busca de Missões")
    st.write("Procure por missões interessantes")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        termo = st.text_input(
            "Digite o termo de busca:",
            placeholder="Ex: Dragão, Floresta, Coleta...",
            label_visibility="collapsed"
        )
    
    with col2:
        buscar = st.button("🔍 Buscar", use_container_width=True, key="btn_busca_miss")
    
    if buscar and termo:
        with st.spinner("🔍 Buscando missões..."):
            try:
                resp = requests.get(
                    f"{API_URL}/buscar_missoes",
                    params={"q": termo},
                    timeout=10
                )
                if resp.status_code == 200:
                    resultado = resp.json()
                else:
                    st.error("Erro na busca")
                    return
            except:
                st.error("Erro ao conectar com a API")
                return
        
        total = resultado.get('total', 0)
        st.success(f"✅ Encontradas {total} missões")
        
        if total > 0:
            missoes = resultado.get('resultados', [])
            
            df_data = []
            for m in missoes:
                df_data.append({
                    'ID': m['id'],
                    'Título': m['titulo'][:50],
                    'Dificuldade': m['dificuldade'],
                    'Ouro': m['recompensa_ouro'],
                    'XP': m['recompensa_experiencia']
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            for m in missoes[:5]:
                with st.expander(f"🎯 {m['titulo']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Dificuldade", m['dificuldade'])
                        st.metric("Nível Mín", m['nivel_minimo'])
                    
                    with col2:
                        st.metric("Ouro", f"{m['recompensa_ouro']}")
                        st.metric("XP", f"{m['recompensa_experiencia']}")
                    
                    with col3:
                        st.metric("Local", m['localizacao'])
                        st.metric("Taxa", f"{m.get('taxa_conclusao_pct', 0):.1f}%")
                    
                    st.write(f"**Objetivo:** {m.get('objetivo', '-')}")

# ============================================================
# PÁGINA: FILTRAR MISSÕES
# ============================================================

def pagina_filtrar_missoes():
    st.header("🎯 Filtrar Missões")
    st.write("Encontre missões que se adequam ao seu nível")
    
    col1, col2 = st.columns(2)
    
    with col1:
        dificuldades = st.multiselect(
            "⚔️ Dificuldade",
            options=["Fácil", "Normal", "Difícil", "Muito Difícil", "Lendário"],
            default=[]
        )
    
    with col2:
        tipos = st.multiselect(
            "🎯 Tipo",
            options=["Eliminar", "Coletar", "Explorar", "Proteger", "Investigar", "Resgate", "Entrega", "Assassinato"],
            default=[]
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        nivel_min = st.number_input("📊 Nível Mínimo", min_value=1, value=1, key="miss_niv_min")
    
    with col2:
        nivel_max = st.number_input("📊 Nível Máximo", min_value=1, value=20, key="miss_niv_max")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ouro_min = st.number_input("💰 Ouro Mínimo", min_value=0, value=0)
    
    with col2:
        ouro_max = st.number_input("💰 Ouro Máximo", min_value=0, value=100000)
    
    if st.button("🔍 Aplicar Filtros", use_container_width=True, type="primary"):
        filtros = {
            'dificuldade': dificuldades[0] if dificuldades else None,
            'tipo': tipos[0] if tipos else None,
            'nivel_min': nivel_min,
            'nivel_max': nivel_max,
            'ouro_min': ouro_min,
            'ouro_max': ouro_max
        }
        filtros = {k: v for k, v in filtros.items() if v is not None}
        
        if filtros:
            with st.spinner("🔍 Filtrando missões..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/filtrar_missoes",
                        json=filtros,
                        timeout=10
                    )
                    if resp.status_code == 200:
                        resultado = resp.json()
                    else:
                        st.error("Erro na filtragem")
                        return
                except:
                    st.error("Erro ao conectar com a API")
                    return
            
            total = resultado.get('total', 0)
            st.success(f"✅ Encontradas {total} missões")
            
            if total > 0:
                missoes = resultado.get('resultados', [])
                
                df_data = []
                for m in missoes:
                    df_data.append({
                        'Título': m['titulo'][:40],
                        'Dificuldade': m['dificuldade'],
                        'Tipo': m['tipo'],
                        'Ouro': m['recompensa_ouro'],
                        'Nível': f"{m['nivel_minimo']}-{m['nivel_maximo']}"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    df['Dificuldade'].value_counts().plot(kind='bar')
                    fig = px.histogram(df, x='Dificuldade', title="Distribuição por Dificuldade")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.scatter(df, x='Ouro', y='Tipo', title="Recompensa por Tipo")
                    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA: DASHBOARD MISSÕES
# ============================================================

def pagina_dashboard_missoes():
    st.header("📊 Dashboard de Missões")
    st.write("Análise completa das missões disponíveis")
    
    with st.spinner("📊 Carregando dashboard..."):
        try:
            resp = requests.get(f"{API_URL}/dashboard_missoes", timeout=10)
            if resp.status_code == 200:
                dados = resp.json()
            else:
                st.error("Erro ao carregar dashboard")
                return
        except:
            st.error("Erro ao conectar com a API")
            return
    
    if dados:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Total de Missões", f"{dados.get('total_missoes', 0)}")
        
        with col2:
            st.metric("💰 Ouro Médio", f"{dados.get('ouro_medio', 0):,.0f}")
        
        with col3:
            st.metric("⭐ XP Médio", f"{dados.get('xp_medio', 0):,.0f}")
        
        with col4:
            st.metric("✨ Taxa Média", f"{dados.get('taxa_media', 0):.1f}%")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            df_dif = pd.DataFrame(dados.get('por_dificuldade', []))
            if not df_dif.empty:
                fig = px.bar(df_dif, x='dificuldade', y='quantidade', title="Missões por Dificuldade")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            df_tipo = pd.DataFrame(dados.get('por_tipo', []))
            if not df_tipo.empty:
                fig = px.pie(df_tipo, names='tipo', values='quantidade', title="Distribuição por Tipo")
                st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PÁGINA: MISSÕES POR DIFICULDADE
# ============================================================

def pagina_missoes_dificuldade():
    st.header("🏆 Missões por Dificuldade")
    
    dificuldades = ["Fácil", "Normal", "Difícil", "Muito Difícil", "Lendário"]
    
    for dif in dificuldades:
        with st.expander(f"⚔️ Missões {dif}"):
            with st.spinner(f"Carregando missões {dif}..."):
                try:
                    resp = requests.get(
                        f"{API_URL}/missoes_dificuldade",
                        params={"dificuldade": dif},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        resultado = resp.json()
                        missoes = resultado.get('missoes', [])
                        
                        if missoes:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total", len(missoes))
                            with col2:
                                st.metric("Ouro Médio", f"{resultado.get('ouro_medio', 0):,}")
                            with col3:
                                st.metric("Taxa", f"{resultado.get('taxa_media', 0):.1f}%")
                            
                            for m in missoes[:10]:
                                st.write(f"🎯 **{m['titulo']}** - {m['recompensa_ouro']} ouro")
                        else:
                            st.info("Nenhuma missão neste nível")
                except:
                    st.error("Erro ao carregar")

# ============================================================
# PÁGINA: GERENCIAR ITENS (CRUD)
# ============================================================

def pagina_gerenciar_itens():
    st.header("⚙️ Gerenciar Itens")
    
    opcao = st.radio("Escolha a operação:", ["Criar", "Atualizar", "Deletar", "Listar"])
    
    if opcao == "Criar":
        st.subheader("✨ Criar Novo Item")
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Item")
            tipo = st.selectbox("Tipo", ["Arma", "Armadura", "Acessório", "Consumível", "Mágico", "Questão"])
        with col2:
            raridade = st.selectbox("Raridade", ["Comum", "Incomum", "Raro", "Épico", "Lendário", "Mítico"])
            valor = st.number_input("Valor (ouro)", min_value=1, value=100)
        
        descricao = st.text_area("Descrição")
        
        if st.button("✅ Criar Item"):
            try:
                data = {
                    "nome": nome,
                    "tipo": tipo,
                    "raridade": raridade,
                    "valor": valor,
                    "descricao": descricao
                }
                resp = requests.post(f"{API_URL}/itens/criar", json=data, timeout=10)
                if resp.status_code == 201:
                    resultado = resp.json()
                    st.success(f"✅ {resultado['mensagem']}")
                    st.json(resultado['item'])
                else:
                    st.error(f"Erro: {resp.json().get('error', 'Desconhecido')}")
            except Exception as e:
                st.error(f"Erro ao conectar: {str(e)}")
    
    elif opcao == "Atualizar":
        st.subheader("🔄 Atualizar Item")
        item_id = st.text_input("ID do Item")
        
        if st.button("🔍 Carregar"):
            try:
                resp = requests.get(f"{API_URL}/itens/{item_id}", timeout=10)
                if resp.status_code == 200:
                    item = resp.json()['item']
                    st.write("Dados atuais:")
                    st.json(item)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_nome = st.text_input("Nome", value=item.get('nome', ''))
                        novo_tipo = st.selectbox("Tipo", ["Arma", "Armadura", "Acessório", "Consumível", "Mágico", "Questão"], 
                                                index=["Arma", "Armadura", "Acessório", "Consumível", "Mágico", "Questão"].index(item.get('tipo', 'Arma')))
                    with col2:
                        novo_raridade = st.selectbox("Raridade", ["Comum", "Incomum", "Raro", "Épico", "Lendário", "Mítico"],
                                                    index=["Comum", "Incomum", "Raro", "Épico", "Lendário", "Mítico"].index(item.get('raridade', 'Comum')))
                        novo_valor = st.number_input("Valor", value=item.get('valor', 0))
                    
                    novo_desc = st.text_area("Descrição", value=item.get('descricao', ''))
                    
                    if st.button("💾 Salvar Alterações"):
                        data = {
                            "nome": novo_nome,
                            "tipo": novo_tipo,
                            "raridade": novo_raridade,
                            "valor": novo_valor,
                            "descricao": novo_desc
                        }
                        resp = requests.put(f"{API_URL}/itens/{item_id}", json=data, timeout=10)
                        if resp.status_code == 200:
                            st.success("✅ Item atualizado com sucesso!")
                        else:
                            st.error(f"Erro: {resp.json().get('error', 'Desconhecido')}")
                else:
                    st.error("Item não encontrado")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Deletar":
        st.subheader("🗑️ Deletar Item")
        item_id = st.text_input("ID do Item a deletar")
        
        if st.button("⚠️ Deletar"):
            try:
                resp = requests.delete(f"{API_URL}/itens/{item_id}", timeout=10)
                if resp.status_code == 200:
                    st.success(f"✅ {resp.json()['mensagem']}")
                else:
                    st.error("Item não encontrado")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Listar":
        st.subheader("📋 Listar Itens")
        pagina = st.number_input("Página", min_value=1, value=1)
        tamanho = st.slider("Itens por página", min_value=5, max_value=50, value=10)
        
        try:
            resp = requests.get(f"{API_URL}/itens", params={"pagina": pagina, "tamanho": tamanho}, timeout=10)
            if resp.status_code == 200:
                resultado = resp.json()
                st.metric("Total de Itens", resultado['total'])
                
                df_data = []
                for item in resultado['itens']:
                    df_data.append({
                        'ID': item['id'],
                        'Nome': item.get('nome', 'N/A'),
                        'Tipo': item.get('tipo', 'N/A'),
                        'Raridade': item.get('raridade', 'N/A'),
                        'Valor': item.get('valor', 0)
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {str(e)}")

# ============================================================
# PÁGINA: GERENCIAR PERSONAGENS (CRUD)
# ============================================================

def pagina_gerenciar_personagens():
    st.header("⚙️ Gerenciar Personagens")
    
    opcao = st.radio("Escolha a operação:", ["Criar", "Atualizar", "Deletar", "Listar"])
    
    if opcao == "Criar":
        st.subheader("✨ Criar Novo Personagem")
        
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome")
            classe = st.selectbox("Classe", ["Guerreiro", "Mago", "Assassino", "Paladino", "Ranger", "Bardo", "Druida", "Clérigo"])
        with col2:
            raca = st.selectbox("Raça", ["Humano", "Elfo", "Anão", "Gnomo", "Meio-Orc", "Meio-Elfo", "Tiefling", "Dracônico"])
            nivel = st.number_input("Nível", min_value=1, max_value=20, value=1)
        
        if st.button("✅ Criar Personagem"):
            try:
                data = {
                    "nome": nome,
                    "classe": classe,
                    "raca": raca,
                    "nivel": nivel,
                    "status": "Ativo"
                }
                resp = requests.post(f"{API_URL}/personagens/criar", json=data, timeout=10)
                if resp.status_code == 201:
                    resultado = resp.json()
                    st.success(f"✅ {resultado['mensagem']}")
                    st.json(resultado['personagem'])
                else:
                    st.error(f"Erro: {resp.json().get('error', 'Desconhecido')}")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Atualizar":
        st.subheader("🔄 Atualizar Personagem")
        pessoa_id = st.text_input("ID do Personagem")
        
        if st.button("🔍 Carregar"):
            try:
                resp = requests.get(f"{API_URL}/personagens/{pessoa_id}", timeout=10)
                if resp.status_code == 200:
                    pessoa = resp.json()['personagem']
                    st.write("Dados atuais:")
                    st.json(pessoa)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_nome = st.text_input("Nome", value=pessoa.get('nome', ''))
                        novo_classe = st.selectbox("Classe", ["Guerreiro", "Mago", "Assassino", "Paladino", "Ranger", "Bardo", "Druida", "Clérigo"],
                                                  index=["Guerreiro", "Mago", "Assassino", "Paladino", "Ranger", "Bardo", "Druida", "Clérigo"].index(pessoa.get('classe', 'Guerreiro')))
                    with col2:
                        novo_raca = st.selectbox("Raça", ["Humano", "Elfo", "Anão", "Gnomo", "Meio-Orc", "Meio-Elfo", "Tiefling", "Dracônico"],
                                                index=["Humano", "Elfo", "Anão", "Gnomo", "Meio-Orc", "Meio-Elfo", "Tiefling", "Dracônico"].index(pessoa.get('raca', 'Humano')))
                        novo_nivel = st.number_input("Nível", min_value=1, max_value=20, value=pessoa.get('nivel', 1))
                    
                    if st.button("💾 Salvar Alterações"):
                        data = {
                            "nome": novo_nome,
                            "classe": novo_classe,
                            "raca": novo_raca,
                            "nivel": novo_nivel,
                            "status": pessoa.get('status', 'Ativo')
                        }
                        resp = requests.put(f"{API_URL}/personagens/{pessoa_id}", json=data, timeout=10)
                        if resp.status_code == 200:
                            st.success("✅ Personagem atualizado com sucesso!")
                        else:
                            st.error(f"Erro: {resp.json().get('error', 'Desconhecido')}")
                else:
                    st.error("Personagem não encontrado")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Deletar":
        st.subheader("🗑️ Deletar Personagem")
        pessoa_id = st.text_input("ID do Personagem a deletar")
        
        if st.button("⚠️ Deletar"):
            try:
                resp = requests.delete(f"{API_URL}/personagens/{pessoa_id}", timeout=10)
                if resp.status_code == 200:
                    st.success(f"✅ {resp.json()['mensagem']}")
                else:
                    st.error("Personagem não encontrado")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Listar":
        st.subheader("📋 Listar Personagens")
        pagina = st.number_input("Página", min_value=1, value=1)
        tamanho = st.slider("Personagens por página", min_value=5, max_value=50, value=10)
        
        try:
            resp = requests.get(f"{API_URL}/personagens", params={"pagina": pagina, "tamanho": tamanho}, timeout=10)
            if resp.status_code == 200:
                resultado = resp.json()
                st.metric("Total de Personagens", resultado['total'])
                
                df_data = []
                for pessoa in resultado['personagens']:
                    df_data.append({
                        'ID': pessoa['id'],
                        'Nome': pessoa.get('nome', 'N/A'),
                        'Classe': pessoa.get('classe', 'N/A'),
                        'Raça': pessoa.get('raca', 'N/A'),
                        'Nível': pessoa.get('nivel', 0)
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {str(e)}")

# ============================================================
# PÁGINA: GERENCIAR MISSÕES (CRUD)
# ============================================================

def pagina_gerenciar_missoes():
    st.header("⚙️ Gerenciar Missões")
    
    opcao = st.radio("Escolha a operação:", ["Criar", "Atualizar", "Deletar", "Listar"])
    
    if opcao == "Criar":
        st.subheader("✨ Criar Nova Missão")
        
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título da Missão")
            dificuldade = st.selectbox("Dificuldade", ["Fácil", "Normal", "Difícil", "Muito Difícil", "Lendário"])
        with col2:
            tipo = st.selectbox("Tipo", ["Eliminar", "Coletar", "Explorar", "Proteger", "Investigar", "Resgate", "Entrega", "Assassinato"])
            recompensa = st.number_input("Recompensa (ouro)", min_value=1, value=500)
        
        descricao = st.text_area("Descrição")
        
        if st.button("✅ Criar Missão"):
            try:
                data = {
                    "titulo": titulo,
                    "dificuldade": dificuldade,
                    "tipo": tipo,
                    "recompensa_ouro": recompensa,
                    "descricao": descricao
                }
                resp = requests.post(f"{API_URL}/missoes/criar", json=data, timeout=10)
                if resp.status_code == 201:
                    resultado = resp.json()
                    st.success(f"✅ {resultado['mensagem']}")
                    st.json(resultado['missao'])
                else:
                    st.error(f"Erro: {resp.json().get('error', 'Desconhecido')}")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Atualizar":
        st.subheader("🔄 Atualizar Missão")
        missao_id = st.text_input("ID da Missão")
        
        if st.button("🔍 Carregar"):
            try:
                resp = requests.get(f"{API_URL}/missoes/{missao_id}", timeout=10)
                if resp.status_code == 200:
                    missao = resp.json()['missao']
                    st.write("Dados atuais:")
                    st.json(missao)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        novo_titulo = st.text_input("Título", value=missao.get('titulo', ''))
                        novo_dificuldade = st.selectbox("Dificuldade", ["Fácil", "Normal", "Difícil", "Muito Difícil", "Lendário"],
                                                       index=["Fácil", "Normal", "Difícil", "Muito Difícil", "Lendário"].index(missao.get('dificuldade', 'Normal')))
                    with col2:
                        novo_tipo = st.selectbox("Tipo", ["Eliminar", "Coletar", "Explorar", "Proteger", "Investigar", "Resgate", "Entrega", "Assassinato"],
                                                index=["Eliminar", "Coletar", "Explorar", "Proteger", "Investigar", "Resgate", "Entrega", "Assassinato"].index(missao.get('tipo', 'Eliminar')))
                        novo_recompensa = st.number_input("Recompensa", value=missao.get('recompensa_ouro', 0))
                    
                    novo_desc = st.text_area("Descrição", value=missao.get('descricao', ''))
                    
                    if st.button("💾 Salvar Alterações"):
                        data = {
                            "titulo": novo_titulo,
                            "dificuldade": novo_dificuldade,
                            "tipo": novo_tipo,
                            "recompensa_ouro": novo_recompensa,
                            "descricao": novo_desc
                        }
                        resp = requests.put(f"{API_URL}/missoes/{missao_id}", json=data, timeout=10)
                        if resp.status_code == 200:
                            st.success("✅ Missão atualizada com sucesso!")
                        else:
                            st.error(f"Erro: {resp.json().get('error', 'Desconhecido')}")
                else:
                    st.error("Missão não encontrada")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Deletar":
        st.subheader("🗑️ Deletar Missão")
        missao_id = st.text_input("ID da Missão a deletar")
        
        if st.button("⚠️ Deletar"):
            try:
                resp = requests.delete(f"{API_URL}/missoes/{missao_id}", timeout=10)
                if resp.status_code == 200:
                    st.success(f"✅ {resp.json()['mensagem']}")
                else:
                    st.error("Missão não encontrada")
            except Exception as e:
                st.error(f"Erro: {str(e)}")
    
    elif opcao == "Listar":
        st.subheader("📋 Listar Missões")
        pagina = st.number_input("Página", min_value=1, value=1)
        tamanho = st.slider("Missões por página", min_value=5, max_value=50, value=10)
        
        try:
            resp = requests.get(f"{API_URL}/missoes", params={"pagina": pagina, "tamanho": tamanho}, timeout=10)
            if resp.status_code == 200:
                resultado = resp.json()
                st.metric("Total de Missões", resultado['total'])
                
                df_data = []
                for missao in resultado['missoes']:
                    df_data.append({
                        'ID': missao['id'],
                        'Título': missao.get('titulo', 'N/A'),
                        'Tipo': missao.get('tipo', 'N/A'),
                        'Dificuldade': missao.get('dificuldade', 'N/A'),
                        'Recompensa': missao.get('recompensa_ouro', 0)
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erro: {str(e)}")

# ============================================================
# RENDERIZAR PÁGINA SELECIONADA
# ============================================================

if modulo == "Itens":
    if pagina == "🔍 Busca Rápida":
        pagina_busca_rapida()
    elif pagina == "🎯 Filtros":
        pagina_filtros()
    elif pagina == "📊 Dashboard":
        pagina_dashboard()
    elif pagina == "🎁 Similares":
        pagina_similares()
    elif pagina == "🔎 Busca Avançada":
        pagina_busca_avancada()
    elif pagina == "⚙️ Gerenciar Itens":
        pagina_gerenciar_itens()

elif modulo == "Personagens":
    if pagina == "🔍 Busca Personagens":
        pagina_busca_personagens()
    elif pagina == "🎯 Filtrar Personagens":
        pagina_filtrar_personagens()
    elif pagina == "📊 Dashboard Personagens":
        pagina_dashboard_personagens()
    elif pagina == "🏆 Top Personagens":
        pagina_top_personagens()
    elif pagina == "⚙️ Gerenciar Personagens":
        pagina_gerenciar_personagens()

elif modulo == "Missões":
    if pagina == "🔍 Busca Missões":
        pagina_busca_missoes()
    elif pagina == "🎯 Filtrar Missões":
        pagina_filtrar_missoes()
    elif pagina == "📊 Dashboard Missões":
        pagina_dashboard_missoes()
    elif pagina == "🏆 Missões por Dificuldade":
        pagina_missoes_dificuldade()
    elif pagina == "⚙️ Gerenciar Missões":
        pagina_gerenciar_missoes()