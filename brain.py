import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import io
import json

# --- CONFIGS ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# LISTA ATUALIZADA - Onde os Big Players jogam pesado
ATIVOS = {
    "GC=F": "Ouro", 
    "CL=F": "Petróleo", 
    "BTC-USD": "Bitcoin", 
    "ETH-USD": "Ethereum",
    "^GSPC": "S&P 500", 
    "NQ=F": "Nasdaq 100",
    "EURUSD=X": "Euro/Dólar",
    "SI=F": "Prata"
}

def gerar_grafico(ticker, nome):
    plt.style.use('dark_background')
    df = yf.download(ticker, period="1d", interval="15m", progress=False)
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df.index, df['Close'], color='#00ff88', linewidth=2)
    ax.set_title(f"Fluxo Institucional - {nome}", color='white')
    ax.grid(color='#333333', linestyle='--')
    buf = io.BytesIO(); plt.savefig(buf, format='png'); buf.seek(0); plt.close()
    return buf

def executar():
    # 1. MONITORAR RESULTADOS
    try:
        r = requests.get(f"{WEBAPP_URL}?acao=get_abertos")
        if r.status_code == 200:
            for ordem in r.json():
                ticker_map = {v: k for k, v in ATIVOS.items()}
                tk = ticker_map.get(ordem['ativo'])
                if not tk: continue
                df_monitor = yf.download(tk, period="1d", interval="1m", progress=False)
                if not df_monitor.empty:
                    preco_atual = round(df_monitor['Close'].iloc[-1:].item(), 4)
                    res = ""
                    if preco_atual >= float(ordem['tp']): res = "💰 TAKE PROFIT"
                    elif preco_atual <= float(ordem['sl']): res = "🛑 STOP LOSS"
                    if res: requests.get(f"{WEBAPP_URL}?acao=fechar&linha={ordem['index']}&resultado={res}")
    except: pass

    # 2. BUSCAR NOVOS SINAIS
    for ticker, nome in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            preco = round(df['Close'].iloc[-1:].item(), 4)
            vol_medio = df['Volume'].mean()
            ultimo_vol = df['Volume'].iloc[-1:].item()
            verde = df['Close'].iloc[-1:].item() > df['Open'].iloc[-1:].item()

            if ultimo_vol > (vol_medio * 1.5): # Aumentei para 1.5x para pegar SÓ o rastro dos GRANDES
                direcao = "COMPRA" if verde else "VENDA"
                dif = preco * 0.004 # Stop curto de 0.4%
                tp = round(preco + (dif * 2) if verde else preco - (dif * 2), 4)
                sl = round(preco - dif if verde else preco + dif, 4)

                check = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={nome}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
                if check.text == "OK":
                    msg = f"🚨 **SINAL DE {direcao}**\n💎 {nome} | 💰 {preco}\n🎯 Alvo: {tp} | 🛑 Stop: {sl}"
                    botoes = {"inline_keyboard": [
                        [{"text": "✅ Gilney Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=gilney"}],
                        [{"text": "✅ Elisete Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=elisete"}]
                    ]}
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={'photo': gerar_grafico(ticker, nome)}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
        except: pass

if __name__ == "__main__": executar()
