import streamlit as st
import sys
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Adiciona o diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa as funções do banco de dados
from db.db_resp_usuario import obter_todas_respostas

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Pesquisa de Satisfação",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Painel de Acompanhamento - Pesquisa de Satisfação do Serviço de Limpeza")

# Função para carregar dados
@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados():
    try:
        respostas = obter_todas_respostas()
        if respostas:
            colunas = ['ID', 'Setor', 'Material Faltando', 'Qual Material', 
                      'Qualidade Serviço', 'Mensagem', 'Data Registro']
            df = pd.DataFrame(respostas, columns=colunas)
            
            # Converte boolean para texto
            df['Material Faltando'] = df['Material Faltando'].map({True: 'Sim', False: 'Não'})
            
            # Converte data para datetime
            df['Data Registro'] = pd.to_datetime(df['Data Registro'])
            
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

# Carrega os dados
df = carregar_dados()

# Botão para atualizar dados
if st.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

if df.empty:
    st.warning("📭 Nenhuma resposta encontrada no banco de dados.")
    st.info("💡 Execute o formulário em `sentimentos/app.py` para gerar dados.")
else:
    # Informações gerais
    st.markdown("---")
    st.subheader("📈 Métricas Gerais")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_respostas = len(df)
        st.metric("🔢 Total de Respostas", total_respostas)
    
    with col2:
        material_faltando = len(df[df['Material Faltando'] == 'Sim'])
        percentual_falta = (material_faltando / total_respostas) * 100 if total_respostas > 0 else 0
        st.metric("🧴 Material Faltando", f"{material_faltando} ({percentual_falta:.1f}%)")
    
    with col3:
        satisfacao_boa = len(df[df['Qualidade Serviço'].isin(['Muito Bom', 'Bom'])])
        percentual_satisfacao = (satisfacao_boa / total_respostas) * 100 if total_respostas > 0 else 0
        st.metric("⭐ Satisfação Positiva", f"{satisfacao_boa} ({percentual_satisfacao:.1f}%)")
    
    with col4:
        # Última resposta
        ultima_resposta = df['Data Registro'].max()
        dias_atras = (datetime.now() - ultima_resposta).days
        st.metric("📅 Última Resposta", f"Há {dias_atras} dias")

    # Gráficos - Linha 1
    st.markdown("---")
    st.subheader("📊 Análise por Setor")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de respostas por setor
        st.markdown("#### 🏢 Respostas por Setor")
        setor_counts = df['Setor'].value_counts()
        
        fig_setor = px.pie(
            values=setor_counts.values, 
            names=setor_counts.index,
            title="Distribuição de Respostas por Setor"
        )
        st.plotly_chart(fig_setor, use_container_width=True)
    
    with col2:
        # Gráfico de qualidade do serviço
        st.markdown("#### ⭐ Avaliação da Qualidade")
        qualidade_counts = df['Qualidade Serviço'].value_counts()
        
        fig_qualidade = px.bar(
            x=qualidade_counts.index,
            y=qualidade_counts.values,
            title="Avaliação da Qualidade do Serviço",
            color=qualidade_counts.values,
            color_continuous_scale="RdYlGn"
        )
        fig_qualidade.update_layout(showlegend=False)
        st.plotly_chart(fig_qualidade, use_container_width=True)

    # Gráficos - Linha 2  
    st.markdown("---")
    st.subheader("🧽 Análise de Materiais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Material faltando por setor
        st.markdown("#### 🏢 Material Faltando por Setor")
        material_setor = pd.crosstab(df['Setor'], df['Material Faltando'])
        
        fig_material_setor = px.bar(
            material_setor, 
            title="Material Faltando por Setor",
            color_discrete_map={'Sim': '#ff6b6b', 'Não': '#51cf66'}
        )
        st.plotly_chart(fig_material_setor, use_container_width=True)
    
    with col2:
        # Tipos de material em falta
        st.markdown("#### 🧴 Tipos de Material em Falta")
        material_falta = df[df['Material Faltando'] == 'Sim']['Qual Material'].value_counts()
        
        if not material_falta.empty:
            fig_tipos = px.bar(
                x=material_falta.values,
                y=material_falta.index,
                orientation='h',
                title="Materiais Mais Solicitados",
                color=material_falta.values,
                color_continuous_scale="Reds"
            )
            fig_tipos.update_layout(showlegend=False)
            st.plotly_chart(fig_tipos, use_container_width=True)
        else:
            st.info("Nenhum material em falta reportado.")

    # Análise temporal
    st.markdown("---")
    st.subheader("📅 Análise Temporal")
    
    # Respostas ao longo do tempo
    df['Data'] = df['Data Registro'].dt.date
    respostas_diarias = df.groupby('Data').size().reset_index(name='Quantidade')
    
    fig_temporal = px.line(
        respostas_diarias, 
        x='Data', 
        y='Quantidade',
        title="Respostas ao Longo do Tempo",
        markers=True
    )
    st.plotly_chart(fig_temporal, use_container_width=True)

    # Heatmap de qualidade por setor usando seaborn
    st.markdown("---")
    st.subheader("🔥 Heatmap - Qualidade por Setor")
    
    # Prepara dados para heatmap
    qualidade_setor = pd.crosstab(df['Setor'], df['Qualidade Serviço'])
    
    # Cria figura matplotlib para seaborn
    fig_heatmap, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(
        qualidade_setor, 
        annot=True, 
        fmt='d', 
        cmap='RdYlGn',
        ax=ax,
        cbar_kws={'label': 'Número de Respostas'}
    )
    ax.set_title('Heatmap: Qualidade do Serviço por Setor')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    st.pyplot(fig_heatmap)

    # Tabela detalhada
    st.markdown("---")
    st.subheader("📋 Dados Detalhados")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        setores_selecionados = st.multiselect(
            "Filtrar por Setor:",
            options=df['Setor'].unique(),
            default=df['Setor'].unique()
        )
    
    with col2:
        qualidade_selecionada = st.multiselect(
            "Filtrar por Qualidade:",
            options=df['Qualidade Serviço'].unique(),
            default=df['Qualidade Serviço'].unique()
        )
    
    with col3:
        material_selecionado = st.selectbox(
            "Filtrar Material Faltando:",
            options=['Todos', 'Sim', 'Não'],
            index=0
        )
    
    # Aplica filtros
    df_filtrado = df[
        (df['Setor'].isin(setores_selecionados)) &
        (df['Qualidade Serviço'].isin(qualidade_selecionada))
    ]
    
    if material_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Material Faltando'] == material_selecionado]
    
    # Mostra tabela filtrada
    st.dataframe(
        df_filtrado[['Setor', 'Material Faltando', 'Qual Material', 'Qualidade Serviço', 'Mensagem', 'Data Registro']], 
        use_container_width=True
    )
    
    # Estatísticas dos dados filtrados
    if not df_filtrado.empty:
        st.markdown("#### 📊 Estatísticas dos Dados Filtrados")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Respostas Filtradas", len(df_filtrado))
        
        with col2:
            media_qualidade = df_filtrado['Qualidade Serviço'].mode()[0] if not df_filtrado.empty else "N/A"
            st.metric("Avaliação Mais Comum", media_qualidade)
        
        with col3:
            material_falta_filtrado = len(df_filtrado[df_filtrado['Material Faltando'] == 'Sim'])
            st.metric("Material Faltando", material_falta_filtrado)

# Rodapé
st.markdown("---")
st.markdown("📊 **Dashboard de Pesquisa de Satisfação** | Atualizado automaticamente a cada 5 minutos")
st.markdown("💡 *Dica: Use os filtros para análises mais específicas*")