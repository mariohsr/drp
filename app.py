import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
import io

# Configuração da Página
st.set_page_config(page_title="Painel DRP - Gestão", layout="wide")

st.title("📊 Painel de Indicadores DRP")
st.markdown("Escolha entre o preenchimento automático por IA ou a inserção manual (Plano B).")

# --- CONFIGURAÇÃO DA API KEY ---
API_KEY = "AIzaSyCoukP-PYLiDw6BMFfKsf--nD3JW72TBFo" 

def analisar_print(image_bytes, key):
    client = genai.Client(api_key=key)
    prompt = """
    Analise a tabela e retorne APENAS um dicionário Python:
    {
        "custo_orcado": float, "custo_realizado": float, "faixas_operacao": int,
        "receita_liq_plano": float, "receita_bruta_plano": float, "receita_bruta_orcada": float,
        "valor_glosa": float, "valor_max_full": float, "dias_operacao": int, 
        "dias_maximos_mes": int, "imagens_aproveitadas": int, "imagens_capturadas": int,
        "data_fechamento": "YYYY-MM-DD", "data_protocolo": "YYYY-MM-DD",
        "valor_imagens_validas": float, "custos_fixos": float, "valor_fatura_mensal": float
    }
    """
    img = Image.open(io.BytesIO(image_bytes))
    response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt, img])
    texto_limpo = response.text.replace("```python", "").replace("```", "").strip()
    return eval(texto_limpo)

def calcular_tudo(d):
    """Função centralizada para os 14 indicadores"""
    kpis = []
    try:
        kpis.append(["1", "% Atingimento do Custo Orçado", f"{(d['custo_realizado']/d['custo_orcado'])*100:.2f}%", "95%"])
        kpis.append(["2", "Valor por Faixa Operada", f"R$ {d['custo_realizado']/d['faixas_operacao']:,.2f}", "MENSUAL"])
        margem = ((d['receita_liq_plano'] - d['custo_realizado']) / d['receita_liq_plano']) * 100
        kpis.append(["3", "Margem de Contribuição %", f"{margem:.2f}%", "MENSUAL"])
        kpis.append(["4", "% Atingimento da Receita Orçada", f"{(d['receita_bruta_plano']/d['receita_bruta_orcada'])*100:.2f}%", "100%"])
        kpis.append(["5", "% Glosa nas medições", f"{(d['valor_glosa']/d['valor_max_full'])*100:.2f}%", "CONTRATO"])
        kpis.append(["6", "% Disponibilidade", f"{(d['dias_operacao']/d['dias_maximos_mes'])*100:.2f}%", "95%"])
        kpis.append(["7", "% Aproveitamento", f"{(d['imagens_aproveitadas']/d['imagens_capturadas'])*100:.2f}%", "90%"])
        
        d1 = pd.to_datetime(d['data_fechamento'])
        d2 = pd.to_datetime(d['data_protocolo'])
        kpis.append(["8", "Dias para protocolo", f"{(d2 - d1).days} Dias", "15 Dias"])
        
        arrec = ((d['valor_imagens_validas'] - d['custos_fixos']) / d['valor_fatura_mensal']) * 100
        kpis.append(["14", "% Arrecadação", f"{arrec:.2f}%", "30%"])
    except:
        return None
    return kpis

# --- INTERFACE EM ABAS ---
aba_ia, aba_manual = st.tabs(["📸 Preencher por Imagem", "⌨️ Inserção Manual (Plano B)"])

with aba_ia:
    st.header("Upload de Print")
    uploaded_file = st.file_uploader("Suba o print da tabela", type=["png", "jpg", "jpeg"], key="ia_upload")
    if uploaded_file:
        try:
            with st.spinner("IA processando..."):
                dados_extraidos = analisar_print(uploaded_file.getvalue(), API_KEY)
                resultados = calcular_tudo(dados_extraidos)
                if resultados:
                    st.table(pd.DataFrame(resultados, columns=["Nº", "Indicador", "Resultado", "Meta"]))
        except Exception as e:
            if "429" in str(e):
                st.error("⚠️ Limite de IA atingido. Use a aba de 'Inserção Manual'.")
            else:
                st.error(f"Erro: {e}")

with aba_manual:
    st.header("Digite os Valores")
    col1, col2 = st.columns(2)
    with col1:
        c_orc = st.number_input("Custo Orçado", value=416861.0)
        c_real = st.number_input("Custo Realizado", value=529585.0)
        faixas = st.number_input("Faixas em Operação", value=265)
        rec_liq = st.number_input("Receita Líquida Plano", value=1776337.0)
    with col2:
        v_glosa = st.number_input("Valor da Glosa", value=87715.17)
        v_max = st.number_input("Valor Máximo Full", value=2195651.99)
        d_op = st.number_input("Dias em Operação", value=28)
        d_mes = st.number_input("Dias no Mês", value=30)
    
    # Botão para calcular manual
    if st.button("Calcular Indicadores Manuais"):
        # Criamos um dicionário no mesmo formato da IA para aproveitar a função de cálculo
        dados_manuais = {
            "custo_orcado": c_orc, "custo_realizado": c_real, "faixas_operacao": faixas,
            "receita_liq_plano": rec_liq, "receita_bruta_plano": 2050000.0, "receita_bruta_orcada": 2071530.0,
            "valor_glosa": v_glosa, "valor_max_full": v_max, "dias_operacao": d_op, 
            "dias_maximos_mes": d_mes, "imagens_aproveitadas": 93, "imagens_capturadas": 100,
            "data_fechamento": "2025-02-01", "data_protocolo": "2025-02-17",
            "valor_imagens_validas": 1500000.0, "custos_fixos": 500000.0, "valor_fatura_mensal": 2000000.0
        }
        res_manual = calcular_tudo(dados_manuais)
        st.table(pd.DataFrame(res_manual, columns=["Nº", "Indicador", "Resultado", "Meta"]))
