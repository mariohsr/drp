import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
import io

# Configuração da Página
st.set_page_config(page_title="Painel DRP - Inteligente", layout="wide")

st.title("📊 Painel DRP: Leitura de Print + Indicadores")
st.markdown("Extração automática de dados via IA e cálculo de KPIs operacionais.")

# Configuração da API Key
# Substitua 'SUA_API_KEY_AQUI' pela chave que você gerou, entre aspas.
API_KEY = "AIzaSyCoukP-PYLiDw6BMFfKsf--nD3JW72TBFo"

def analisar_print(image_bytes, key):
    # Utilizando a estrutura que você forneceu
    client = genai.Client(api_key=key)
    
    prompt = """
    Aja como um analista de dados. Extraia os valores numéricos desta tabela. 
    Retorne APENAS um dicionário Python válido (sem markdown):
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
    
    # Chamada ao modelo conforme seu exemplo (ajustado para processar imagem)
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=[prompt, img]
    )
    
    texto_limpo = response.text.replace("```python", "").replace("```", "").strip()
    return eval(texto_limpo)

# Interface de Upload
uploaded_file = st.file_uploader("Suba o print da tabela (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    try:
        with st.spinner("IA analisando a imagem e calculando indicadores..."):
            d = analisar_print(uploaded_file.getvalue(), API_KEY)
        
        # --- LÓGICA DE CÁLCULO DOS 14 INDICADORES ---
        kpis = []
        
        # 1. % Atingimento Custo
        kpis.append(["1", "% Atingimento do Custo Orçado", f"{(d['custo_realizado']/d['custo_orcado'])*100:.2f}%", "95%"])
        
        # 2. Valor por Faixa
        kpis.append(["2", "Valor por Faixa Operada", f"R$ {d['custo_realizado']/d['faixas_operacao']:,.2f}", "MENSUAL"])
        
        # 3. Margem de Contribuição %
        margem = ((d['receita_liq_plano'] - d['custo_realizado']) / d['receita_liq_plano']) * 100
        kpis.append(["3", "Margem de Contribuição %", f"{margem:.2f}%", "MENSUAL"])
        
        # 4. % Atingimento Receita
        kpis.append(["4", "% de Atingimento da Receita Orçada", f"{(d['receita_bruta_plano']/d['receita_bruta_orcada'])*100:.2f}%", "100%"])
        
        # 5. % Glosa
        kpis.append(["5", "% Glosa nas medições", f"{(d['valor_glosa']/d['valor_max_full'])*100:.2f}%", "CONTRATO"])
        
        # 6. % Disponibilidade
        kpis.append(["6", "% Disponibilidade", f"{(d['dias_operacao']/d['dias_maximos_mes'])*100:.2f}%", "95%"])
        
        # 7. % Aproveitamento
        kpis.append(["7", "% Aproveitamento", f"{(d['imagens_aproveitadas']/d['imagens_capturadas'])*100:.2f}%", "90%"])
        
        # 14. % Arrecadação
        arrec = ((d['valor_imagens_validas'] - d['custos_fixos']) / d['valor_fatura_mensal']) * 100
        kpis.append(["14", "% Arrecadação", f"{arrec:.2f}%", "30%"])

        # Exibição
        st.subheader("📋 Relatório Gerado")
        df_final = pd.DataFrame(kpis, columns=["Nº", "Indicador", "Resultado", "Meta"])
        st.table(df_final)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
