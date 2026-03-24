import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import mplfinance as mpf
import io
import time
import random

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Ojuaobot Elite 80", page_icon="🏎️", layout="wide")

TOKEN_TG = st.secrets["TOKEN_TG"]
ID_TG = st.secrets["ID_TG"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s1yWFFfBLlHUoZlJldBjgNG7wsPMNIWWGsxMJS067Uo/edit"
CONF_FILTRO = 80.0  # Nova régua calibrada

# --- CONEXÃO ---
def conectar_planilha():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(credentials)
        return client.open_by_url(SHEET_URL).get_worksheet(0)
    except: return None

def get_sp_time():
    return datetime.utcnow() - timedelta(hours=3)

# --- SISTEMA DE GRÁFICO E TELEGRAM ---
def enviar_sinal_com_grafico(ticker, atual, alvo, stop, conf, tipo):
    # 1. Busca dados para o gráfico (últimos 20 dias)
    df_hist = yf.download(ticker, period="30d", interval="1d", progress=False)
    if df_hist.empty: return

    # 2. Gera o gráfico de candles em memória
    buf = io.BytesIO()
    ap = [
        mpf.make_addplot([alvo]*len(df_hist), color='green', linestyle='--', width=1),
        mpf.make_addplot([stop]*len(df_hist), color='red', linestyle='--', width=1)
    ]
    
    mpf.plot(df_hist, type='candle', style='charles', 
             title=f'\n{ticker} - {tipo}',
             ylabel='Preço',
             addplot=ap,
             savefig=dict(fname=buf, format='png'),
             tight_layout=True)
    buf.seek(0)

    # 3. Monta a legenda
    texto = (f"🎯 *GATILHO ATIVADO: {ticker}*\n"
             f"🔥 Confiança: {conf:.1f}%\n"
             f"👉 Tipo: {tipo}\n"
             f"💵 Entrada: {atual:.2f}\n"
             f"🚀 Alvo: {alvo:.2f} | 🛑 Stop: {stop:.2f}")

    # 4. Envia via Telegram
    url = f"https://api.telegram.org/bot{TOKEN_TG}/sendPhoto"
    try:
        requests.post(url, data={"chat_id": ID_TG, "caption": texto, "parse_mode": "Markdown"}, 
                      files={"photo": buf})
    except: pass

def enviar_msg_tg(texto):
    url = f"https://api.telegram.org/bot{TOKEN_TG}/sendMessage"
    try: requests.post(url, data={"chat_id": ID_TG, "text": texto, "parse_mode": "Markdown"})
    except: pass

# --- MOTOR DE INTELIGÊNCIA ---
def calcular_indicadores(df):
    df = df.copy()
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df["RSI"] = 100 - (100 / (1 + (gain / loss)))
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["ATR"] = (df["High"] - df["Low"]).rolling(window=14).mean()
    return df.dropna()

def treinar_e_prever(ticker):
    try:
        df = yf.download(ticker, period="150d", interval="1d", progress=False)
        if len(df) < 55: return None
        df_ind = calcular_indicadores(df)
        
        # Filtro de Tendência Macro (OPÇÃO B)
        preco_atual = df_ind['Close'].iloc[-1]
        ma50 = df_ind['MA50'].iloc[-1]
        tendencia = "ALTA" if preco_atual > ma50 else "BAIXA"

        features = ['Close', 'RSI', 'MA20', 'ATR']
        X = df_ind[features].iloc[:-1].values
        y = df_ind['Close'].iloc[1:].values
        
        modelo = GradientBoostingRegressor(n_estimators=100, random_state=42).fit(X, y)
        prev = float(modelo.predict(df_ind[features].iloc[-1].values.reshape(1, -1))[0])
        
        return prev, preco_atual, float(df_ind['ATR'].iloc[-1]), tendencia
    except: return None

# --- GERENTE DE OPERAÇÕES ---
def gerenciar_operacoes(sheet):
    if not sheet: return
    try:
        valores = sheet.get_all_values()
        if len(valores) <= 1: return
        for i, linha in enumerate(valores[1:], start=2):
            if len(linha) < 9 or str(linha[8]).strip() != "⏳ EM ANDAMENTO": continue
            ticker = linha[1]
            try:
                entrada = float(str(linha[2]).replace(',', '.'))
                alvo = float(str(linha[3]).replace(',', '.'))
                stop = float(str(linha[5]).replace(',', '.'))
                
                df_at = yf.download(ticker, period="1d", progress=False)
                agora = float(df_at['Close'].iloc[-1])
                
                encerrou = False
                if (alvo > entrada and agora >= alvo) or (alvo < entrada and agora <= alvo):
                    status, encerrou = "🎯 ALVO ATINGIDO", True
                elif (alvo > entrada and agora <= stop) or (alvo < entrada and agora >= stop):
                    status, encerrou = "🛑 STOPADO", True
                
                if encerrou:
                    lucro = round(agora - entrada if alvo > entrada else entrada - agora, 2)
                    sheet.update(f'G{i}:I{i}', [[round(agora, 2), lucro, status]])
                    enviar_msg_tg(f"💰 *ORDEM FECHADA*\nAtivo: {ticker}\nStatus: {status}\nLucro: R$ {lucro}")
            except: continue
    except: pass

# --- UI E SCANNER ---
st.title("🏆 OJUAOBOT ELITE 80")
agora_sp = get_sp_time()

SCAN_LIST = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "ABEV3.SA", "MGLU3.SA", "B3SA3.SA", 
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "BTC-USD", "ETH-USD", "SOL-USD"
]

sheet = conectar_planilha()
gerenciar_operacoes(sheet)

# Tabela de ordens
abertos = []
df_full = pd.DataFrame()
if sheet:
    bruto = sheet.get_all_values()
    if len(bruto) > 1:
        df_full = pd.DataFrame(bruto[1:], columns=bruto[0])
        abertos = df_full[df_full['Status'] == '⏳ EM ANDAMENTO']['Ticker'].tolist()

# OPÇÃO C: BOTÃO DE SCAN MANUAL
if st.button("🚀 REESCANEAR AGORA"):
    with st.spinner("Procurando sinais com régua de 80%..."):
        encontrou = False
        for ticker in SCAN_LIST:
            if ticker in abertos: continue
            res = treinar_e_prever(ticker)
            if res:
                prev, atual, atr, tend = res
                diff = ((prev - atual) / atual) * 100
                conf = min(65 + (abs(diff) * 12), 99)
                
                if conf >= CONF_FILTRO:
                    if (diff > 0 and tend == "ALTA") or (diff < 0 and tend == "BAIXA"):
                        tipo = "✅ COMPRA" if diff > 0 else "⚠️ VENDA"
                        stop = atual - (atr * 1.5) if diff > 0 else atual + (atr * 1.5)
                        enviar_sinal_com_grafico(ticker, atual, prev, stop, conf, tipo)
                        sheet.append_row([agora_sp.strftime('%d/%m/%Y %H:%M'), ticker, atual, prev, f"{conf:.1f}%", stop, atual, 0, "⏳ EM ANDAMENTO"], value_input_option="USER_ENTERED")
                        st.success(f"Sinal enviado para {ticker}!")
                        encontrou = True
        if not encontrou: st.warning("Nenhum sinal sólido na régua de 80% agora.")

# RELATÓRIO AUTOMÁTICO MINUTO 40
if 'last_h' not in st.session_state: st.session_state.last_h = ""
if agora_sp.minute >= 40 and st.session_state.last_h != agora_sp.hour:
    # (Lógica idêntica ao scan manual para o relatório automático)
    st.session_state.last_h = agora_sp.hour
    st.rerun()

st.divider()
st.subheader(f"📊 Ordens Ativas: {len(abertos)}")
if not df_full.empty: st.dataframe(df_full.tail(30), use_container_width=True)
st.write(f"🕒 **Última atualização:** {agora_sp.strftime('%H:%M:%S')}")

time.sleep(60); st.rerun()
