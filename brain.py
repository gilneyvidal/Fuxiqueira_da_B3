import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import io
import json

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

ATIVOS = {"GC=F": "Ouro", "SI=F": "Prata", "HG=F": "Cobre", "BTC-USD": "Bitcoin", "^GSPC": "S&P 500"}

def gerar_grafico(ticker, nome):
    plt.style.use('dark_background')
    df = yf.download(ticker, period="1d", interval="15m", progress=False)
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df.index, df['Close'], color='#00ff88', linewidth=2)
    ax.set_title(f"Fluxo Institucional - {nome}", color='white')
    buf = io.BytesIO(); plt.savefig(buf, format='png'); buf.seek(0); plt.close()
    return buf

def executar():
    # 1. MONITORAR RESULTADOS DOS ABERTOS
    try:
        r = requests.get(f"{WEBAPP_URL}?acao=get_abertos")
        for ordem in r.json():
            ticker_map = {v: k for k, v in ATIVOS.items()}
            preco_atual = round(float(yf.download(ticker_map[ordem['ativo']], period="1d", interval="1m", progress=False)['Close'].iloc[-1]), 2)
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
            preco = round(float(df['Close'].iloc[-1]), 2)
            if float(df['Volume'].iloc[-1]) > (float(df['Volume'].mean()) * 1.3):
                verde = df['Close'].iloc[-1] > df['Open'].iloc[-1]
                direcao = "COMPRA" if verde else "VENDA"
                tp = round(preco * 1.01 if verde else preco * 0.99, 2)
                sl = round(preco * 0.995 if verde else preco * 1.005, 2)

                check = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={nome}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
                if check.text == "OK":
                    msg = f"🚨 **SINAL DE {direcao}**\n💎 {nome} | 💰 {preco}\n🎯 Alvo: {tp} | 🛑 Stop: {sl}"
                    botoes = {"inline_keyboard": [[{"text": "✅ Gilney Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=gilney"}],
                                                 [{"text": "✅ Elisete Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=elisete"}]]}
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={'photo': gerar_grafico(ticker, nome)}, data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
        except: pass

if __name__ == "__main__": executar()
