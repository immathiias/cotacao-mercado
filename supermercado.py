import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Painel Supermercado - Cotações", layout="wide")

DADOS_FILE = "cotacoes.csv"
FORN_FILE = "fornecedores.json"

def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# Autenticação por Senha
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.subheader("Acesso Restrito ao Supermercado")
    senha = st.text_input("Introduza a senha de acesso:", type="password")
    if st.button("Entrar"):
        if senha == "SOBRINHO2026":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# --- Painel de Controlo Principal (Apenas se autenticado) ---
st.title("📊 Painel de Resultados da Cotação")

# Gerador de links para enviar no WhatsApp
st.subheader("🔗 Links Exclusivos dos Fornecedores")
fornecedores = carregar_json(FORN_FILE)
# Substitua pelo link real quando publicar no Streamlit Cloud
LINK_BASE_VENDEDOR = "https://streamlit.app" 

cols = st.columns(3)
for i, (chave, info) in enumerate(fornecedores.items()):
    status = "🔴 Bloqueado (Já enviou)" if info["bloqueado"] else "🟢 Disponível"
    link_completo = f"{LINK_BASE_VENDEDOR}/?token={chave}"
    cols[i % 3].markdown(f"**{info['nome']}** ({status})<br>`{link_completo}`", unsafe_allow_html=True)

st.markdown("---")

# Exibição dos Resultados
if os.path.exists(DADOS_FILE):
    df_cotacoes = pd.read_csv(DADOS_FILE)
    if not df_cotacoes.empty:
        pivot_df = df_cotacoes.pivot(index="Produto", columns="Fornecedor", values="Preco")
        
        vencedores_lista, menores_precos = [], []
        for prod in pivot_df.index:
            precos_validos = pivot_df.loc[prod][pivot_df.loc[prod] > 0].dropna()
            if not precos_validos.empty:
                vencedores_lista.append(precos_validos.idxmin())
                menores_precos.append(f"R$ {precos_validos.min():.2f}")
            else:
                vencedores_lista.append("Sem stock")
                menores_precos.append("-")
                
        pivot_df.insert(0, "Preço Vencedor", menores_precos)
        pivot_df.insert(0, "Fornecedor Vencedor", vencedores_lista)
        
        st.dataframe(pivot_df.style.highlight_min(axis=1, color="#D4EDDA", subset=pivot_df.columns[2:]))
    else:
        st.info("Nenhum preço registado no ficheiro de cotações.")
else:
    st.info("Aguardando os primeiros envios dos fornecedores.")

# Reset Semanal
st.markdown("---")
if st.button("🔴 Reiniciar Todas as Cotações e Desbloquear Vendedores"):
    if os.path.exists(DADOS_FILE):
        os.remove(DADOS_FILE)
    for k in fornecedores:
        fornecedores[k]["bloqueado"] = False
    salvar_json(FORN_FILE, fornecedores)
    st.success("Dados limpos e acessos libertados para a nova semana!")
    st.rerun()
