import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import json

# --- CONFIGS ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Ativos de Alta Volatilidade (Onde os Big Players jogam)
ATIVOS = {
    "GC=F": "Ouro", "CL=F": "Petróleo", "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum",
    "^GSPC": "S&P 500", "NQ=F": "Nasdaq 100", "EURUSD=X": "Euro/Dólar", "SI=F": "Prata"
}

def gerar_grafico_profissional(df, nome, tp, sl, entrada):
    mc = mpf.make_marketcolors(up='#00ff88', down='#ff3355', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, gridcolor='#333333', facecolor='black')
    hlines_config = dict(hlines=[float(tp), float(sl), float(entrada)], 
                         colors=['#00ff00', '#ff0000', '#0088ff'], 
                         linestyle=['-', '-', '--'], linewidths=[1.5, 1.5, 1.0])
    buf = io.BytesIO()
    mpf.plot(df, type='candle', style=s, title=f"\nFluxo Institucional - {nome}",
             ylabel='Preco', hlines=hlines_config, savefig=dict(fname=buf, format='png', bbox_inches='tight'), figsize=(10, 6))
    buf.seek(0)
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
                    if isinstance(df_monitor.columns, pd.MultiIndex): df_monitor.columns = df_monitor.columns.get_level_values(0)
                    preco_atual = round(float(df_monitor['Close'].iloc[-1]), 4)
                    res = ""
                    if preco_atual >= float(ordem['tp']): res = "💰 TAKE PROFIT"
                    elif preco_atual <= float(ordem['sl']): res = "🛑 STOP LOSS"
                    if res: requests.get(f"{WEBAPP_URL}?acao=fechar&linha={ordem['index']}&resultado={res}")
    except: pass

    # 2. BUSCAR NOVOS SINAIS (Régua 1.3x)
    for ticker, nome in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            for c in ['Open', 'High', 'Low', 'Close']: df[c] = pd.to_numeric(df[c], errors='coerce')
            df = df.dropna()

            preco = round(float(df['Close'].iloc[-1]), 4)
            vol_medio = df['Volume'].mean()
            ultimo_vol = df['Volume'].iloc[-1]
            verde = df['Close'].iloc[-1] > df['Open'].iloc[-1]

            if ultimo_vol > (vol_medio * 1.3): # CALIBRAGEM 1.3x
                direcao = "COMPRA" if verde else "VENDA"
                dif = preco * 0.005
                tp = round(preco + (dif * 2) if verde else preco - (dif * 2), 4)
                sl = round(preco - dif if verde else preco + dif, 4)

                check = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={nome}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
                if check.text == "OK":
                    msg = f"🚨 **SINAL DE {direcao}**\n💎 **{nome}** | 💰 **Entrada:** {preco}\n🎯 **Alvo:** {tp} | 🛑 **Stop:** {sl}"
                    botoes = {"inline_keyboard": [[{"text": "✅ Gilney Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=gilney"}],
                                                  [{"text": "✅ Elisete Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=elisete"}]]}
                    foto = gerar_grafico_profissional(df.tail(40), nome, tp, sl, preco)
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={'photo': foto}, 
                                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
        except: pass

if __name__ == "__main__": executar()
