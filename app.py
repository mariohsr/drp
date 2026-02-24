import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

# Configuração da Página
st.set_page_config(page_title="Painel DRP - Inteligente", layout="wide")

st.title("📊 Calculadora DRP: Leitura de Print + KPIs")
st.markdown("Suba o print da sua tabela e o sistema extrairá os dados e calculará os indicadores automaticamente.")

# Configuração da API Key (Deve ser inserida nos Secrets do Streamlit ou no Sidebar)
with st.sidebar:
    st.header("Configuração")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha uma chave gratuita em: aistudio.google.com")

# --- FUNÇÃO DE PROCESSAMENTO DE IMAGEM ---
def extrair_dados_com_ai(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Analise a imagem desta tabela e extraia os seguintes valores numéricos. 
    Responda APENAS no formato de dicionário Python, sem textos extras:
    {
        'custo_orcado': valor,
        'custo_realizado': valor,
        'faixas_operacao': valor,
        'receita_liq_realizada': valor,
        'receita_bruta_planejada': valor,
        'receita_bruta_realizada': valor,
        'valor_glosa': valor,
        'valor_max_full': valor,
        'valor_imagens_validas': valor,
        'custos_fixos': valor,
        'valor_fatura_mensal': valor
    }
    """
    img = Image.open(io.BytesIO(image_bytes))
    response = model.generate_content([prompt, img])
    return eval(response.text.replace("```python", "").replace("```", ""))

# --- INTERFACE DE UPLOAD ---
uploaded_file = st.file_uploader("Arraste o print da tabela aqui", type=["png", "jpg", "jpeg"])

if uploaded_file and api_key:
    with st.spinner("Analisando imagem com IA..."):
        try:
            dados = extrair_dados_com_ai(uploaded_file.getvalue(), api_key)
            st.success("Dados extraídos com sucesso!")
            
            # --- CÁLCULOS DOS 14 INDICADORES ---
            resultados = []
            
            # 1. % Atingimento Custo
            ating_custo = (dados['custo_realizado'] / dados['custo_orcado']) * 100
            resultados.append(["1. % Atingimento Custo Orçado", f"{ating_custo:.2f}%", "95%"])
            
            # 2. Valor por Faixa
            v_faixa = dados['custo_realizado'] / dados['faixas_operacao']
            resultados.append(["2. Valor por Faixa Operada", f"R$ {v_faixa:,.2f}", "MENSUAL"])
            
            # 3. Margem de Contribuição
            margem = ((dados['receita_liq_realizada'] - dados['custo_realizado']) / dados['receita_liq_realizada']) * 100
            resultados.append(["3. Margem de Contribuição %", f"{margem:.2f}%", "MENSUAL"])
            
            # 4. Atingimento Receita
            ating_rec = (dados['receita_bruta_planejada'] / dados['receita_bruta_realizada']) * 100
            resultados.append(["4. % Atingimento Receita Orçada", f"{ating_rec:.2f}%", "100%"])
            
            # 5. % Glosa
            perc_glosa = (dados['valor_glosa'] / dados['valor_max_full']) * 100
            resultados.append(["5. % Glosa nas medições", f"{perc_glosa:.2f}%", "CONTRATO"])

            # 14. % Arrecadação
            arrecadacao = ((dados['valor_imagens_validas'] - dados['custos_fixos']) / dados['valor_fatura_mensal']) * 100
            resultados.append(["14. % Arrecadação", f"{arrecadacao:.2f}%", "30%"])

            # Exibição em Tabela
            df_final = pd.DataFrame(resultados, columns=["Indicador", "Resultado", "Meta"])
            st.table(df_final)
            
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
elif not api_key and uploaded_file:
    st.warning("Por favor, insira a API Key no menu lateral para processar a imagem.")
