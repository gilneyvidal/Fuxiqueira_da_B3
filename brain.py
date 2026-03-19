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

# Ativos Selecionados (M15)
ATIVOS = {"GC=F": "Ouro", "SI=F": "Prata", "HG=F": "Cobre", "BTC-USD": "Bitcoin", "^GSPC": "S&P 500"}

def gerar_grafico(ticker, nome):
    plt.style.use('dark_background')
    df = yf.download(ticker, period="1d", interval="15m", progress=False)
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df.index, df['Close'], color='#00ff88', linewidth=2)
    ax.set_title(f"Fluxo Institucional - {nome}", color='white')
    ax.grid(color='#333333', linestyle='--')
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def executar():
    # 1. MONITORAR RESULTADOS DOS ABERTOS
    try:
        r = requests.get(f"{WEBAPP_URL}?acao=get_abertos")
        if r.status_code == 200:
            for ordem in r.json():
                ticker_map = {v: k for k, v in ATIVOS.items()}
                df_monitor = yf.download(ticker_map[ordem['ativo']], period="1d", interval="1m", progress=False)
                if not df_monitor.empty:
                    # Uso do .item() evita o aviso de FutureWarning
                    preco_atual = round(df_monitor['Close'].iloc[-1:].item(), 2)
                    res = ""
                    if preco_atual >= float(ordem['tp']): res = "💰 TAKE PROFIT"
                    elif preco_atual <= float(ordem['sl']): res = "🛑 STOP LOSS"
                    
                    if res:
                        requests.get(f"{WEBAPP_URL}?acao=fechar&linha={ordem['index']}&resultado={res}")
    except:
        pass

    # 2. BUSCAR NOVOS SINAIS
    for ticker, nome in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            # Ajuste para evitar os avisos do Python
            preco = round(df['Close'].iloc[-1:].item(), 2)
            vol_medio = df['Volume'].mean()
            ultimo_vol = df['Volume'].iloc[-1:].item()
            vela_verde = df['Close'].iloc[-1:].item() > df['Open'].iloc[-1:].item()

            if ultimo_vol > (vol_medio * 1.3): # Filtro SMC
                direcao = "COMPRA" if vela_verde else "VENDA"
                # Gestão 2:1
                dif = preco * 0.005
                tp = round(preco + (dif * 2) if vela_verde else preco - (dif * 2), 2)
                sl = round(preco - dif if vela_verde else preco + dif, 2)

                check = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={nome}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
                
                if check.text == "OK":
                    msg = (f"🚨 **SINAL DE {direcao}**\n\n"
                           f"💎 **Ativo:** {nome}\n"
                           f"💰 **Preço:** {preco}\n"
                           f"🎯 **Alvo (2:1):** {tp}\n"
                           f"🛑 **Stop:** {sl}\n\n"
                           f"👇 Quem entrou nessa?")
                    
                    botoes = {"inline_keyboard": [
                        [{"text": "✅ Gilney Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=gilney"}],
                        [{"text": "✅ Elisete Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={nome}&quem=elisete"}]
                    ]}
                    
                    foto = gerar_grafico(ticker, nome)
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  files={'photo': foto}, 
                                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
        except:
            pass

if __name__ == "__main__":
    executar()
