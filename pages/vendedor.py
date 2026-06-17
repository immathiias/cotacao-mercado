import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Envio de Cotação de Frios")
st.markdown(
    """
    <style>
        [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

PRODUTOS_FILE = "produtos.txt"
DADOS_FILE = "cotacoes.csv"
FORN_FILE = "fornecedores.json"

def carregar_produtos():
    if os.path.exists(PRODUTOS_FILE):
        with open(PRODUTOS_FILE, "r", encoding="utf-8") as f:
            return [l.strip() for l in f.readlines() if l.strip()]
    return []

def carregar_json(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

query_params = st.query_params
token_usuario = query_params.get("token", None)

fornecedores = carregar_json(FORN_FILE)

if not token_usuario or token_usuario not in fornecedores:
    st.error("❌ Link inválido ou expirado. Solicite um novo link ao supermercado.")
    st.stop()

info_fornecedor = fornecedores[token_usuario]
nome_fornecedor = info_fornecedor["nome"]

if info_fornecedor["bloqueado"]:
    st.success(f"🎉 Obrigado, {nome_fornecedor}! A sua cotação desta semana já foi processada.")
    st.stop()

st.title(f"📋 Cotação Semanal - {nome_fornecedor}")
st.write("Insira os valores item por item. Deixe 0,00 nos produtos indisponíveis.")

produtos = carregar_produtos()

if not produtos:
    st.warning("O supermercado ainda não definiu a lista de produtos para esta semana.")
    st.stop()

precos_inputs = {}

# Cria uma caixa de preço separada para cada item da lista criada pelo supermercado
for prod in produtos:
    precos_inputs[prod] = st.number_input(f"Preço para: {prod} (R$)", min_value=0.0, value=0.0, step=0.10, key=f"v_{prod}")

if st.button("Gravar e Enviar Preços", type="primary"):
    novos_dados = []
    for prod, preco in precos_inputs.items():
        if preco > 0:
            novos_dados.append({"Fornecedor": nome_fornecedor, "Produto": prod, "Preco": preco})
            
    if novos_dados:
        df_existente = pd.read_csv(DADOS_FILE) if os.path.exists(DADOS_FILE) else pd.DataFrame(columns=["Fornecedor", "Produto", "Preco"])
        if not df_existente.empty:
            df_existente = df_existente[df_existente["Fornecedor"] != nome_fornecedor]
        df_final = pd.concat([df_existente, pd.DataFrame(novos_dados)], ignore_index=True)
        df_final.to_csv(DADOS_FILE, index=False)
        
        fornecedores[token_usuario]["bloqueado"] = True
        with open(FORN_FILE, "w", encoding="utf-8") as f:
            json.dump(fornecedores, f, indent=4, ensure_ascii=False)
            
        st.success("Cotação gravada com sucesso!")
        st.rerun()
    else:
        st.warning("Preencha pelo menos um preço válido para conseguir enviar.")
