import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image
import io

st.set_page_config(page_title="Gestão DRP - Inteligente", layout="wide")

# Interface Principal
st.title("📊 Calculadora DRP: Leitura de Print + KPIs")
st.markdown("Extraia dados de prints e calcule os 14 indicadores automaticamente.")

# Configuração da API no Sidebar
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha uma chave gratuita em: aistudio.google.com")

# Função para Processar Imagem com IA
def analisar_tabela(image_bytes, key):
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Aja como um analista de dados. Extraia os seguintes valores desta tabela de indicadores. 
    Retorne APENAS um dicionário Python válido:
    {
        "custo_orcado": float,
        "custo_realizado": float,
        "faixas_operacao": int,
        "receita_liq_plano": float,
        "receita_bruta_plano": float,
        "receita_bruta_orcada": float,
        "valor_glosa": float,
        "valor_max_full": float,
        "dias_operacao": int,
        "dias_maximos_mes": int,
        "imagens_aproveitadas": int,
        "imagens_capturadas": int,
        "data_fechamento": "YYYY-MM-DD",
        "data_protocolo": "YYYY-MM-DD",
        "envios_prazo": int,
        "documentos_necessarios": int,
        "faixas_reprovadas": int,
        "total_verificacoes": int,
        "valor_imagens_validas": float,
        "custos_fixos": float,
        "valor_fatura_mensal": float
    }
    """
    img = Image.open(io.BytesIO(image_bytes))
    response = model.generate_content([prompt, img])
    # Limpeza simples para garantir que o eval funcione
    texto_limpo = response.text.replace("```python", "").replace("```", "").strip()
    return eval(texto_limpo)

# Upload do Arquivo
uploaded_file = st.file_uploader("Arraste o print da tabela aqui", type=["png", "jpg", "jpeg"])

if uploaded_file and api_key:
    try:
        with st.spinner("IA Analisando o print..."):
            d = analisar_tabela(uploaded_file.getvalue(), api_key)
        
        st.success("Dados extraídos!")
        
        # --- Lógica de Cálculo dos 14 KPIs ---
        kpis = []
        # 1 a 5 (Financeiros)
        kpis.append(["1. % Atingimento Custo Orçado", f"{(d['custo_realizado']/d['custo_orcado'])*100:.2f}%", "95%"])
        kpis.append(["2. Valor por Faixa Operada", f"R$ {d['custo_realizado']/d['faixas_operacao']:,.2f}", "MENSUAL"])
        kpis.append(["3. Margem de Contribuição %", f"{((d['receita_liq_plano'] - d['custo_realizado'])/d['receita_liq_plano'])*100:.2f}%", "MENSUAL"])
        kpis.append(["4. % Atingimento Receita Orçada", f"{(d['receita_bruta_plano']/d['receita_bruta_orcada'])*100:.2f}%", "100%"])
        kpis.append(["5. % Glosa nas medições", f"{(d['valor_glosa']/d['valor_max_full'])*100:.2f}%", "CONTRATO"])
        
        # 6 a 13 (Operacionais)
        kpis.append(["6. % Disponibilidade", f"{(d['dias_operacao']/d['dias_maximos_mes'])*100:.2f}%", "95%"])
        kpis.append(["7. % Aproveitamento", f"{(d['imagens_aproveitadas']/d['imagens_capturadas'])*100:.2f}%", "90%"])
        
        # Diferença de datas para item 8
        d1 = pd.to_datetime(d['data_fechamento'])
        d2 = pd.to_datetime(d['data_protocolo'])
        dias_prot = (d2 - d1).days
        kpis.append(["8. Dias para protocolo", f"{dias_prot} dias", "15 dias"])
        
        kpis.append(["9. Prazo de Aprovação", "0 Dias (Detran-PA)", "30/45/60"])
        kpis.append(["10. % Atendimento Calendário", f"{(d['envios_prazo']/d['documentos_necessarios'])*100:.2f}%", "100%"])
        kpis.append(["11. % Reprovação Aferições", f"{(d['faixas_reprovadas']/d['total_verificacoes'])*100:.2f}%", "2%"])
        kpis.append(["12. % Tempo Resolução", "Aguardando Dados", "95%"])
        kpis.append(["13. Tempo Aprovação Registros", "Aguardando Dados", "3 dias"])
        
        # 14 (Arrecadação)
        arrec = ((d['valor_imagens_validas'] - d['custos_fixos']) / d['valor_fatura_mensal']) * 100
        kpis.append(["14. % Arrecadação", f"{arrec:.2f}%", "30%"])

        # Exibição
        df_final = pd.DataFrame(kpis, columns=["Indicador", "Resultado", "Meta"])
        st.table(df_final)

    except Exception as e:
        st.error(f"Erro ao processar imagem. Verifique se a API Key é válida. Detalhe: {e}")
