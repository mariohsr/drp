import streamlit as st
import pandas as pd
from google import genai
from PIL import Image
import io

# Configuração da página
st.set_page_config(page_title="Gestão DRP - Inteligente", layout="wide")

st.title("📊 Painel DRP: Leitura de Print + Indicadores")
st.markdown("Extração automática de dados via IA e cálculo de KPIs operacionais.")

# Barra lateral para configuração
with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = st.text_input("Insira sua Gemini API Key:", type="password")
    st.info("Obtenha sua chave em: aistudio.google.com")
    st.markdown("---")
    st.write("Desenvolvido para gestão de indicadores DRP.")

# Função para processar a imagem usando a nova biblioteca genai
def analisar_print(image_bytes, key):
    client = genai.Client(api_key=key)
    
    prompt = """
    Aja como um analista de dados. Extraia os valores numéricos desta tabela de indicadores. 
    Retorne APENAS um dicionário Python (sem markdown ou texto extra):
    {
        "custo_orcado": float,
        "custo_realizado": float,
        "faixas_operacao": int,
        "receita_liq_realizada": float,
        "receita_bruta_planejada": float,
        "receita_bruta_realizada": float,
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
    
    # Converte bytes para objeto de imagem
    img = Image.open(io.BytesIO(image_bytes))
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, img]
    )
    
    # Limpa a resposta para garantir que seja um dicionário válido
    texto_limpo = response.text.replace("```python", "").replace("```", "").strip()
    return eval(texto_limpo)

# Área de Upload
uploaded_file = st.file_uploader("Suba o print da tabela (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file and api_key:
    try:
        with st.spinner("IA analisando a imagem e extraindo dados..."):
            dados = analisar_print(uploaded_file.getvalue(), api_key)
        
        st.success("Dados extraídos com sucesso!")
        
        # --- CÁLCULO DOS INDICADORES (Baseado na sua imagem) ---
        kpis = []
        
        # 1. % Atingimento Custo
        kpis.append(["1. % Atingimento Custo Orçado", f"{(dados['custo_realizado']/dados['custo_orcado'])*100:.2f}%", "95%"])
        
        # 2. Valor por Faixa
        kpis.append(["2. Valor por Faixa Operada", f"R$ {dados['custo_realizado']/dados['faixas_operacao']:,.2f}", "MENSUAL"])
        
        # 3. Margem de Contribuição % (Receita Liq - Custo Realizado) / Receita Liq
        margem = ((dados['receita_liq_realizada'] - dados['custo_realizado']) / dados['receita_liq_realizada']) * 100
        kpis.append(["3. Margem de Contribuição %", f"{margem:.2f}%", "MENSUAL"])
        
        # 4. % Atingimento Receita
        kpis.append(["4. % Atingimento Receita Orçada", f"{(dados['receita_bruta_planejada']/dados['receita_bruta_realizada'])*100:.2f}%", "100%"])
        
        # 5. % Glosa
        kpis.append(["5. % Glosa nas medições", f"{(dados['valor_glosa']/dados['valor_max_full'])*100:.2f}%", "CONTRATO"])
        
        # 6. % Disponibilidade
        kpis.append(["6. % Disponibilidade", f"{(dados['dias_operacao']/dados['dias_maximos_mes'])*100:.2f}%", "95%"])
        
        # 7. % Aproveitamento
        kpis.append(["7. % Aproveitamento", f"{(dados['imagens_aproveitadas']/dados['imagens_capturadas'])*100:.2f}%", "90%"])
        
        # 8. Dias para protocolo
        d1 = pd.to_datetime(dados['data_fechamento'])
        d2 = pd.to_datetime(dados['data_protocolo'])
        dias_prot = (d2 - d1).days
        kpis.append(["8. Dias para protocolo", f"{dias_prot} Dias", "15 Dias"])
        
        # 14. % Arrecadação
        arrec = ((dados['valor_imagens_validas'] - dados['custos_fixos']) / dados['valor_fatura_mensal']) * 100
        kpis.append(["14. % Arrecadação", f"{arrec:.2f}%", "30%"])

        # Exibição da Tabela Final
        st.subheader("📋 Relatório Gerado")
        df_final = pd.DataFrame(kpis, columns=["Indicador", "Resultado", "Meta"])
        st.table(df_final)

    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        st.info("Dica: Certifique-se de que a API Key é válida e que o print está legível.")

elif not api_key and uploaded_file:
    st.warning("⚠️ Insira a sua API Key na barra lateral para ativar a leitura do print.")
