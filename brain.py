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
ATIVOS = {
    "GC=F": "Ouro",
    "SI=F": "Prata",
    "HG=F": "Cobre",
    "BTC-USD": "Bitcoin",
    "^GSPC": "S&P 500"
}

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
    for ticker, nome in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            preco = round(float(df['Close'].iloc[-1]), 2)
            vol_medio = float(df['Volume'].mean())
            ultimo_vol = float(df['Volume'].iloc[-1])
            vela_verde = df['Close'].iloc[-1] > df['Open'].iloc[-1]

            if ultimo_vol > (vol_medio * 1.3): # Gatilho de Volume SMC
                direcao = "COMPRA (LONG)" if vela_verde else "VENDA (SHORT)"
                # Gestão de Risco 2:1
                dif = preco * 0.005 # 0.5% de stop
                tp = round(preco + (dif * 2) if vela_verde else preco - (dif * 2), 2)
                sl = round(preco - dif if vela_verde else preco + dif, 2)

                # PERGUNTA PARA A PLANILHA SE PODE MANDAR
                check = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={nome}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
                
                if check.text == "OK":
                    msg = (f"🚨 **DOSSIÊ {direcao}**\n\n"
                           f"💎 **Ativo:** {nome}\n"
                           f"💰 **Preço:** {preco}\n"
                           f"🎯 **Alvo (2:1):** {tp}\n"
                           f"🛑 **Stop Técnico:** {sl}\n\n"
                           f"👇 Gilney, entrou nessa?")
                    
                    link_sim = f"{WEBAPP_URL}?acao=posicionado&ativo={nome}"
                    botoes = {"inline_keyboard": [[{"text": "✅ ESTOU POSICIONADO", "url": link_sim}],
                                                 [{"text": "❌ NÃO ENTREI", "url": "https://t.me/"}]]}
                    
                    foto = gerar_grafico(ticker, nome)
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                                  files={'photo': foto}, 
                                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
        except: pass

if __name__ == "__main__":
    executar()
