import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
import requests
import time
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import random

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Ojuaobot Elite Stable", page_icon="🏆", layout="wide")

TOKEN_TG = st.secrets["TOKEN_TG"]
ID_TG = st.secrets["ID_TG"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1s1yWFFfBLlHUoZlJldBjgNG7wsPMNIWWGsxMJS067Uo/edit"
CONF_FILTRO = 85.0

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

def enviar_tg(texto):
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
        if len(df) < 50: return None
        df_ind = calcular_indicadores(df)
        
        preco_atual = df_ind['Close'].iloc[-1]
        ma50 = df_ind['MA50'].iloc[-1]
        tendencia = "ALTA" if preco_atual > ma50 else "BAIXA"

        features = ['Close', 'RSI', 'MA20', 'ATR']
        X = df_ind[features].iloc[:-1].values
        y = df_ind['Close'].iloc[1:].values
        
        modelo = GradientBoostingRegressor(n_estimators=100, random_state=42).fit(X, y)
        last_row = df_ind[features].iloc[-1].values.reshape(1, -1)
        prev = float(modelo.predict(last_row)[0])
        
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
                
                finalizou = False
                if (alvo > entrada and agora >= alvo) or (alvo < entrada and agora <= alvo):
                    status, finalizou = "🎯 ALVO ATINGIDO", True
                elif (alvo > entrada and agora <= stop) or (alvo < entrada and agora >= stop):
                    status, finalizou = "🛑 STOPADO", True
                
                if finalizou:
                    lucro = round(agora - entrada if alvo > entrada else entrada - agora, 2)
                    sheet.update(f'G{i}:I{i}', [[round(agora, 2), lucro, status]])
                    enviar_tg(f"💰 *ORDEM FECHADA*\nAtivo: {ticker}\nResultado: {status}\nLucro: R$ {lucro}")
            except: continue
    except: pass

# --- UI PRINCIPAL ---
st.title("🏆 OJUAOBOT ELITE STABLE")
agora_sp = get_sp_time()
st.write(f"🕒 **Status:** Online | {agora_sp.strftime('%H:%M:%S')}")

SCAN_LIST = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "ABEV3.SA", "MGLU3.SA", "B3SA3.SA", "HAPV3.SA", "ELET3.SA", 
    "WEGE3.SA", "RENT3.SA", "SUZB3.SA", "JBSS3.SA", "RAIL3.SA", "GGBR4.SA", "CSNA3.SA", "COGN3.SA", "AZUL4.SA", "LREN3.SA",
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "PYPL", "ADBE", "INTC", "AMD", "BABA", "DIS", "V", "MA", 
    "JPM", "BAC", "PFE", "KO", "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOT-USD", "LINK-USD", "DOGE-USD"
]

sheet = conectar_planilha()
gerenciar_operacoes(sheet)

# Carregar dados da planilha para a tabela
abertos = []
df_full = pd.DataFrame()
if sheet:
    bruto = sheet.get_all_values()
    if len(bruto) > 1:
        df_full = pd.DataFrame(bruto[1:], columns=bruto[0])
        abertos = df_full[df_full['Status'] == '⏳ EM ANDAMENTO']['Ticker'].tolist()

# BOTÃO DE SCAN MANUAL
if st.button("🚀 REESCANEAR AGORA"):
    st.info("Iniciando scan manual em 50 ativos...")
    sinais_manuais = []
    for ticker in SCAN_LIST:
        res = treinar_e_prever(ticker)
        if res:
            prev, atual, atr, tend = res
            diff = ((prev - atual) / atual) * 100
            conf = min(65 + (abs(diff) * 12), 99)
            if conf >= CONF_FILTRO:
                if (diff > 0 and tend == "ALTA") or (diff < 0 and tend == "BAIXA"):
                    sinais_manuais.append({"t": ticker, "tp": "✅ COMPRA" if diff > 0 else "⚠️ VENDA", "c": conf})
    if sinais_manuais:
        for s in sinais_manuais: st.success(f"{s['tp']} detectado para {s['t']} ({s['c']:.1f}%)")
    else: st.warning("Nenhuma oportunidade sólida encontrada agora.")

# RELATÓRIO MINUTO 40
if 'last_h' not in st.session_state: st.session_state.last_h = ""
cur_h = agora_sp.strftime("%H")

if agora_sp.minute >= 40 and st.session_state.last_h != cur_h:
    sinais_hora = []
    for ticker in SCAN_LIST:
        res = treinar_e_prever(ticker)
        if res:
            prev, atual, atr, tend = res
            diff = ((prev - atual) / atual) * 100
            conf = min(65 + (abs(diff) * 12), 99)
            if conf >= CONF_FILTRO and ((diff > 0 and tend == "ALTA") or (diff < 0 and tend == "BAIXA")):
                sinais_hora.append({"t": ticker, "a": atual, "p": prev, "s": (atual-(atr*1.5) if diff > 0 else atual+(atr*1.5)), "tp": "✅ COMPRA" if diff > 0 else "⚠️ VENDA", "c": conf})
    
    if sinais_hora:
        msg = f"🏆 *RELATÓRIO OJUAOBOT - {agora_sp.strftime('%H:40')}*\n"
        for s in sinais_hora:
            msg += f"🔹 *{s['t']}* ({s['c']:.1f}%)\n👉 {s['tp']} | Alvo: {s['p']:.2f}\n\n"
            sheet.append_row([agora_sp.strftime('%d/%m/%Y %H:%M'), s['t'], s['a'], s['p'], f"{s['c']:.1f}%", s['s'], s['a'], 0, "⏳ EM ANDAMENTO"], value_input_option="USER_ENTERED")
        enviar_tg(msg)
    else:
        enviar_tg(f"⚖️ *STATUS OJUAOBOT*: {len(abertos)} ordens ativas. Sem novos sinais agora. 🛡️")
    st.session_state.last_h = cur_h

# --- AQUI ESTÁ A TABELA QUE SUMIU! ---
st.divider()
st.subheader(f"📊 Ordens Ativas: {len(abertos)}")
if not df_full.empty:
    st.dataframe(df_full.tail(50), use_container_width=True)
else:
    st.write("Aguardando conexão com a planilha...")

st.write(f"🕒 **Última atualização:** {agora_sp.strftime('%H:%M:%S')}")
time.sleep(60); st.rerun()
