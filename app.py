import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
import io

# Configuração da Página para o projeto DRP
st.set_page_config(page_title="Gestão DRP - Final", layout="wide")

st.title("📊 Painel de Indicadores DRP")
st.markdown("Escolha entre o preenchimento automático por IA ou a inserção manual (Plano B).")

# --- CONFIGURAÇÃO DA API KEY INTEGRADA ---
API_KEY = "xxx" 

def analisar_print(image_bytes, key):
    """Função para extrair dados da imagem usando o modelo estável 1.5 Flash"""
    client = genai.Client(api_key=key)
    prompt = """
    Aja como um analista de dados. Extraia os valores numéricos desta tabela de indicadores. 
    Retorne APENAS um dicionário Python válido, sem markdown:
    {
        "custo_orcado": float, "custo_realizado": float, "faixas_operacao": int,
        "receita_liq_plano": float, "receita_bruta_plano": float, "receita_bruta_orcada": float,
        "valor_glosa": float, "valor_max_full": float, "dias_operacao": int, 
        "dias_maximos_mes": int, "imagens_aproveitadas": int, "imagens_capturadas": int,
        "data_fechamento": "YYYY-MM-DD", "data_protocolo": "YYYY-MM-DD",
        "envios_prazo": int, "documentos_necessarios": int, "faixas_reprovadas": int,
        "total_verificacoes": int, "valor_imagens_validas": float, "custos_fixos": float,
        "valor_fatura_mensal": float
    }
    """
    img = Image.open(io.BytesIO(image_bytes))

    #Evitar error 404
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=[prompt, img]
    )
    
    texto_limpo = response.text.replace("```python", "").replace("```", "").strip()
    return eval(texto_limpo)

def gerar_tabela_kpis(d):
    """Lógica de cálculo baseada na imagem de indicadores"""
    kpis = []
    try:
        # Cálculos conforme a tabela oficial fornecida
        kpis.append(["1", "% Atingimento do Custo Orçado", f"{(d['custo_realizado']/d['custo_orcado'])*100:.2f}%", "95%"])
        kpis.append(["2", "Valor por Faixa Operada", f"R$ {d['custo_realizado']/d['faixas_operacao']:,.2f}", "MENSUAL"])
        margem = ((d['receita_liq_plano'] - d['custo_realizado']) / d['receita_liq_plano']) * 100
        kpis.append(["3", "Margem de Contribuição %", f"{margem:.2f}%", "MENSUAL"])
        kpis.append(["4", "% Atingimento da Receita Orçada", f"{(d['receita_bruta_plano']/d['receita_bruta_orcada'])*100:.2f}%", "100%"])
        kpis.append(["5", "% Glosa nas medições", f"{(d['valor_glosa']/d['valor_max_full'])*100:.2f}%", "CONTRATO"])
        kpis.append(["6", "% Disponibilidade", f"{(d['dias_operacao']/d['dias_maximos_mes'])*100:.2f}%", "95%"])
        kpis.append(["7", "% Aproveitamento", f"{(d['imagens_aproveitadas']/d['imagens_capturadas'])*100:.2f}%", "90%"])
        
        d1, d2 = pd.to_datetime(d['data_fechamento']), pd.to_datetime(d['data_protocolo'])
        kpis.append(["8", "Dias para protocolo da medição", f"{(d2 - d1).days} Dias", "15 Dias"])
        
        arrec = ((d['valor_imagens_validas'] - d['custos_fixos']) / d['valor_fatura_mensal']) * 100
        kpis.append(["14", "% Arrecadação", f"{arrec:.2f}%", "30%"])
        return kpis
    except Exception: return None

# --- ESTRUTURA DE ABAS ---
tab_ia, tab_manual = st.tabs(["📸 Preencher por Imagem", "⌨️ Inserção Manual (Plano B)"])

with tab_ia:
    st.subheader("Upload de Print")
    uploaded_file = st.file_uploader("Arraste o print da tabela aqui", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        try:
            with st.spinner("IA analisando imagem..."):
                dados = analisar_print(uploaded_file.getvalue(), API_KEY)
                res = gerar_tabela_kpis(dados)
                if res: 
                    st.success("Cálculos concluídos!")
                    st.table(pd.DataFrame(res, columns=["Nº", "Indicador", "Resultado", "Meta"]))
        except Exception as e:
            if "429" in str(e): 
                st.error("⚠️ Cota de IA atingida. Use a aba de inserção manual.")
            elif "404" in str(e):
                st.error("❌ Erro de versão do modelo. Tente novamente em instantes.")
            else: 
                st.error(f"Erro: {e}")

with tab_manual:
    st.subheader("Entrada Manual")
    col1, col2 = st.columns(2)
    with col1:
        c_orc = st.number_input("Custo Orçado", value=416861.0)
        c_real = st.number_input("Custo Realizado", value=529585.0)
        faixas = st.number_input("Faixas em Operação", value=265)
    with col2:
        v_glosa = st.number_input("Valor Glosa", value=87715.17)
        v_max = st.number_input("Valor Máximo", value=2195651.99)
        d_op = st.number_input("Dias Operação", value=28)
    
    if st.button("Calcular Manualmente"):
        d_man = {
            "custo_orcado": c_orc, "custo_realizado": c_real, "faixas_operacao": faixas,
            "receita_liq_plano": 1776337.0, "receita_bruta_plano": 2050000.0, "receita_bruta_orcada": 2071530.0,
            "valor_glosa": v_glosa, "valor_max_full": v_max, "dias_operacao": d_op, "dias_maximos_mes": 30,
            "imagens_aproveitadas": 93, "imagens_capturadas": 100, "data_fechamento": "2025-02-01", 
            "data_protocolo": "2025-02-17", "valor_imagens_validas": 1500000.0, "custos_fixos": 500000.0, "valor_fatura_mensal": 2000000.0
        }
        res_m = gerar_tabela_kpis(d_man)
        st.table(pd.DataFrame(res_m, columns=["Nº", "Indicador", "Resultado", "Meta"]))
