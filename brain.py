import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import json
from datetime import datetime
import pytz

# --- CONFIGS ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Mapeamento: Ticker_Yahoo -> [Nome_Exibicao, Ticker_Busca_Plataforma]
ATIVOS = {
    "GC=F": ["Ouro", "XAUUSD"],
    "CL=F": ["Petróleo", "WTI"],
    "BTC-USD": ["Bitcoin", "BTCUSD"],
    "ETH-USD": ["Ethereum", "ETHUSD"],
    "^GSPC": ["S&P 500", "US500"],
    "NQ=F": ["Nasdaq 100", "USTEC"],
    "EURUSD=X": ["Euro/Dólar", "EURUSD"],
    "SI=F": ["Prata", "XAGUSD"]
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
    fuso = pytz.timezone('America/Sao_Paulo')
    
    # 1. MONITORAR RESULTADOS
    try:
        r = requests.get(f"{WEBAPP_URL}?acao=get_abertos")
        if r.status_code == 200:
            for ordem in r.json():
                tk_yahoo = next((k for k, v in ATIVOS.items() if v[0] == ordem['ativo']), None)
                if not tk_yahoo: continue
                df_monitor = yf.download(tk_yahoo, period="1d", interval="1m", progress=False)
                if not df_monitor.empty:
                    if isinstance(df_monitor.columns, pd.MultiIndex): df_monitor.columns = df_monitor.columns.get_level_values(0)
                    preco_atual = round(float(df_monitor['Close'].iloc[-1]), 4)
                    res = ""
                    if preco_atual >= float(ordem['tp']): res = "💰 TAKE PROFIT"
                    elif preco_atual <= float(ordem['sl']): res = "🛑 STOP LOSS"
                    if res: requests.get(f"{WEBAPP_URL}?acao=fechar&linha={ordem['index']}&resultado={res}")
    except: pass

    # 2. BUSCAR NOVOS SINAIS
    for tk_yahoo, info in ATIVOS.items():
        nome_exibicao, ticker_busca = info[0], info[1]
        try:
            df = yf.download(tk_yahoo, period="2d", interval="15m", progress=False)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.dropna()

            preco = round(float(df['Close'].iloc[-1]), 4)
            vol_medio = df['Volume'].mean()
            ultimo_vol = df['Volume'].iloc[-1]
            verde = df['Close'].iloc[-1] > df['Open'].iloc[-1]
            
            # Captura data/hora do candle atual
            data_hora_candle = df.index[-1].astimezone(fuso).strftime('%d/%m/%Y - %H:%M')

            if ultimo_vol > (vol_medio * 1.3): 
                direcao = "COMPRA" if verde else "VENDA"
                dif = preco * 0.005 
                tp = round(preco + (dif * 2) if verde else preco - (dif * 2), 4)
                sl = round(preco - dif if verde else preco + dif, 4)

                check = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={nome_exibicao}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
                if check.text == "OK":
                    msg = (f"🚨 **SINAL DE {direcao} ({ticker_busca})**\n"
                           f"📅 **Data/Hora:** {data_hora_candle}\n"
                           f"💎 {nome_exibicao} | 💰 **Entrada:** {preco}\n"
                           f"🎯 **Alvo:** {tp} | 🛑 **Stop:** {sl}")
                    
                    botoes = {"inline_keyboard": [[{"text": "✅ Gilney Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome_exibicao}&quem=gilney"}],
                                                  [{"text": "✅ Elisete Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome_exibicao}&quem=elisete"}]]}
                    
                    foto = gerar_grafico_profissional(df.tail(40), nome_exibicao, tp, sl, preco)
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", files={'photo': foto}, 
                                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
        except: pass

if __name__ == "__main__": executar()
