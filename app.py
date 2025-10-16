import streamlit as st
import pandas as pd
from datetime import datetime
import os
from extratores.gastos_vereadores import extrair_gastos_vereadores
from extratores.comissoes_votacoes import extrair_comissoes_votacoes
from extratores.projetos_tramitacao import extrair_projetos_tramitacao

# Configuração da página
st.set_page_config(
    page_title="Extrator de Dados - Câmara Municipal SP",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("📊 Extrator de Dados - Câmara Municipal de São Paulo")
st.markdown("---")

# Sidebar para seleção
st.sidebar.header("⚙️ Configurações")

# Seleção do tipo de extração
tipo_extracao = st.sidebar.selectbox(
    "Selecione o tipo de extração:",
    ["Gastos de Vereadores", "Comissões e Votações", "Projetos em Tramitação"]
)

st.sidebar.markdown("---")

# Configurações comuns
ano_atual = datetime.now().year
ano = st.sidebar.number_input(
    "Ano:",
    min_value=2020,
    max_value=ano_atual,
    value=ano_atual,
    step=1
)

# Interface específica para cada tipo de extração
if tipo_extracao == "Gastos de Vereadores":
    st.header("💰 Extração de Gastos de Vereadores")
    st.info("Este extrator coleta informações sobre gastos dos vereadores da Câmara Municipal de São Paulo.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        mes_inicio = st.selectbox(
            "Mês Inicial:",
            range(1, 13),
            format_func=lambda x: f"{x:02d} - {['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][x-1]}"
        )
    
    with col2:
        mes_fim = st.selectbox(
            "Mês Final:",
            range(mes_inicio, 13),
            format_func=lambda x: f"{x:02d} - {['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][x-1]}"
        )
    
    if st.button("🚀 Iniciar Extração", type="primary", use_container_width=True):
        with st.spinner(f"Extraindo dados de {mes_inicio:02d}/{ano} até {mes_fim:02d}/{ano}..."):
            try:
                resultado = extrair_gastos_vereadores(ano, mes_inicio, mes_fim)
                
                if resultado['sucesso']:
                    st.success(f"✅ Extração concluída com sucesso!")
                    st.success(f"📁 Arquivo gerado: {resultado['arquivo_excel']}")
                    
                    # Exibir estatísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Registros", resultado['total_registros'])
                    with col2:
                        st.metric("Vereadores", resultado['total_vereadores'])
                    with col3:
                        st.metric("Tempo de Execução", f"{resultado['tempo_execucao']:.2f}s")
                    
                    # Visualizar preview dos dados
                    if os.path.exists(resultado['arquivo_excel']):
                        df_preview = pd.read_excel(resultado['arquivo_excel'])
                        st.subheader("📋 Preview dos Dados")
                        st.dataframe(df_preview.head(50), use_container_width=True)
                        
                        # Botão de download
                        with open(resultado['arquivo_excel'], 'rb') as f:
                            st.download_button(
                                label="⬇️ Baixar Planilha Excel",
                                data=f,
                                file_name=os.path.basename(resultado['arquivo_excel']),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.error(f"❌ Erro na extração: {resultado['erro']}")
                    
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")

elif tipo_extracao == "Comissões e Votações":
    st.header("🗳️ Extração de Comissões e Votações")
    st.info("Este extrator coleta informações sobre comissões e votações de projetos dos vereadores.")
    
    # Lista de tipos de projeto
    tipos_projeto = {
        "Todos": "TODOS",
        "PL - Projeto de Lei": "PL",
        "PDL - Projeto de Decreto Legislativo": "PDL",
        "PEC - Proposta de Emenda à Constituição": "PEC",
        "PRC - Projeto de Resolução": "PRC",
        "REQ - Requerimento": "REQ",
        "IND - Indicação": "IND",
        "MOC - Moção": "MOC",
        "SUB - Substitutivo": "SUB"
    }
    
    tipo_selecionado = st.sidebar.selectbox(
        "Tipo de Projeto:",
        options=list(tipos_projeto.keys()),
        help="Selecione o tipo de projeto ou 'Todos' para extrair todos os tipos"
    )
    
    tipo_projeto = tipos_projeto[tipo_selecionado]
    
    # Mostrar info sobre a seleção
    if tipo_projeto == "TODOS":
        st.warning("⚠️ Todos os tipos de projet foram selecionados, a extração pode demorar um pouco mais que o normal")
        st.info(f"📊 Serão extraídos {len(tipos_projeto) - 1} tipos de projetos do ano {ano}")
    else:
        st.info(f"📊 Extraindo dados de {tipo_selecionado} do ano {ano}")
    
    if st.button("🚀 Iniciar Extração", type="primary", use_container_width=True):
        with st.spinner(f"Extraindo dados..."):
            try:
                resultado = extrair_comissoes_votacoes(ano, tipo_projeto)
                
                if resultado['sucesso']:
                    st.success(f"✅ Extração concluída com sucesso!")
                    
                    if tipo_projeto == "TODOS":
                        st.success(f"📁 {resultado['total_tipos']} tipos de projetos foram extraídos!")
                        st.success(f"📁 Arquivo consolidado: {resultado['arquivo_excel']}")
                    else:
                        st.success(f"📁 Arquivo gerado: {resultado['arquivo_excel']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total de Registros", resultado['total_registros'])
                    with col2:
                        st.metric("Tempo de Execução", f"{resultado['tempo_execucao']:.2f}s")
                    
                    # Visualizar preview
                    if os.path.exists(resultado['arquivo_excel']):
                        df_preview = pd.read_excel(resultado['arquivo_excel'])
                        st.subheader("📋 Preview dos Dados")
                        st.dataframe(df_preview.head(50), use_container_width=True)
                        
                        # Estatísticas adicionais
                        if 'Parlamentar' in df_preview.columns:
                            st.subheader("📊 Estatísticas")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Total de Parlamentares", df_preview['Parlamentar'].nunique())
                            with col2:
                                if 'Comissão' in df_preview.columns:
                                    st.metric("Total de Comissões", df_preview['Comissão'].nunique())
                        
                        with open(resultado['arquivo_excel'], 'rb') as f:
                            st.download_button(
                                label="⬇️ Baixar Planilha Excel",
                                data=f,
                                file_name=os.path.basename(resultado['arquivo_excel']),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.error(f"❌ Erro na extração: {resultado['erro']}")
                    
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

elif tipo_extracao == "Projetos em Tramitação":
    st.header("📜 Extração de Projetos em Tramitação")
    st.info("Este extrator coleta informações sobre projetos em tramitação na Câmara Municipal.")
    
    tipo_projeto = st.sidebar.text_input(
        "Tipo de Projeto:",
        value="PL",
        help="Ex: PL, PDL, PEC, etc."
    )
    
    if st.button("🚀 Iniciar Extração", type="primary", use_container_width=True):
        with st.spinner(f"Extraindo dados de {tipo_projeto} do ano {ano}..."):
            try:
                resultado = extrair_projetos_tramitacao(ano, tipo_projeto)
                
                if resultado['sucesso']:
                    st.success(f"✅ Extração concluída com sucesso!")
                    st.success(f"📁 Arquivo gerado: {resultado['arquivo_excel']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total de Projetos", resultado['total_projetos'])
                    with col2:
                        st.metric("Tempo de Execução", f"{resultado['tempo_execucao']:.2f}s")
                    
                    # Visualizar preview
                    if os.path.exists(resultado['arquivo_excel']):
                        df_preview = pd.read_excel(resultado['arquivo_excel'])
                        st.subheader("📋 Preview dos Dados")
                        st.dataframe(df_preview.head(50), use_container_width=True)
                        
                        with open(resultado['arquivo_excel'], 'rb') as f:
                            st.download_button(
                                label="⬇️ Baixar Planilha Excel",
                                data=f,
                                file_name=os.path.basename(resultado['arquivo_excel']),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.error(f"❌ Erro na extração: {resultado['erro']}")
                    
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")

# Rodapé
st.markdown("---")
st.markdown("**Desenvolvido para extração de dados públicos da Câmara Municipal de São Paulo**")
