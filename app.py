import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calculadora de KPIs Operacionais", layout="wide")

st.title("📊 Painel de Indicadores Operacionais")
st.markdown("Insira os dados abaixo para calcular os KPIs conforme a tabela padrão.")

# Organizando a entrada de dados em colunas para facilitar a visualização
with st.sidebar:
    st.header("📥 Dados de Entrada")
    
    st.subheader("Custos (Sem Intercompany)")
    custo_orcado = st.number_input("Custo Orçado", value=416861.0)
    custo_realizado = st.number_input("Custo Realizado", value=529585.0)
    faixas_operacao = st.number_input("Quant. Faixas em Operação", value=265)
    
    st.subheader("Receitas e Margem")
    receita_liq_plano = st.number_input("Receita Líquida Plano", value=1776337.0)
    custo_operacional = st.number_input("Custo Operacional", value=529585.0)
    receita_bruta_plano = st.number_input("Receita Bruta Plano", value=2050000.0)
    receita_bruta_orcada = st.number_input("Receita Bruta Orçada", value=2071530.0)
    
    st.subheader("Glosas e Faturamento")
    valor_glosa = st.number_input("Valor Glosa", value=87715.17)
    valor_max_full = st.number_input("Valor Máximo/Full", value=2195651.99)
    valor_fatura_mensal = st.number_input("Valor da Fatura Mensal", value=2000000.0)
    valor_imagens_validas = st.number_input("Valor Imagens Válidas", value=1500000.0)
    custos_fixos = st.number_input("Custos Fixos", value=500000.0)

# Lógica de Cálculo baseada na IMAGEM
# ----------------------------------
kpis = {}
# 1. % Atingimento Custo
kpis['1. % Atingimento Custo Orçado'] = (custo_realizado / custo_orcado) * 100
# 2. Valor por Faixa Operada
kpis['2. Valor por Faixa Operada'] = custo_realizado / faixas_operacao
# 3. Margem de Contribuição %
kpis['3. Margem de Contribuição %'] = ((receita_liq_plano - custo_operacional) / receita_liq_plano) * 100
# 4. % Atingimento Receita Orçada
kpis['4. % Atingimento Receita Orçada'] = (receita_bruta_plano / receita_bruta_orcada) * 100
# 5. % Glosa nas medições
kpis['5. % Glosa nas medições'] = (valor_glosa / valor_max_full) * 100
# 14. % Arrecadação
kpis['14. % Arrecadação'] = ((valor_imagens_validas - custos_fixos) / valor_fatura_mensal) * 100

# Exibição
st.header("📋 Relatório de Indicadores")
df_res = pd.DataFrame(list(kpis.items()), columns=['Indicador', 'Resultado Calculado'])

# Formatação visual
st.table(df_res.style.format({"Resultado Calculado": "{:.2f}"}))

# Destaques em cards
c1, c2, c3 = st.columns(3)
c1.metric("Atingimento Custo", f"{kpis['1. % Atingimento Custo Orçado']:.2f}%", delta_color="inverse")
c2.metric("Margem Contribuição", f"{kpis['3. Margem de Contribuição %']:.2f}%")
c3.metric("Glosa", f"{kpis['5. % Glosa nas medições']:.2f}%", delta_color="inverse")
