import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import time
import io

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Watchlist Expandida (Commodities e Metais)
ATIVOS = {
    "GC=F": {"nome": "Ouro", "tp": 0.01, "sl": 0.005},
    "SI=F": {"nome": "Prata", "tp": 0.015, "sl": 0.008},
    "HG=F": {"nome": "Cobre", "tp": 0.012, "sl": 0.006},
    "REMX": {"nome": "Terras Raras", "tp": 0.02, "sl": 0.01},
    "BTC-USD": {"nome": "Bitcoin", "tp": 0.02, "sl": 0.01},
    "^GSPC": {"nome": "S&P 500", "tp": 0.006, "sl": 0.003}
}

def gerar_grafico_dark(ticker, nome):
    plt.style.use('dark_background')
    data = yf.download(ticker, period="1d", interval="15m", progress=False)
    if data.empty: return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data.index, data['Close'], color='#00ff88', linewidth=2)
    ax.fill_between(data.index, data['Close'], color='#00ff88', alpha=0.1)
    ax.set_title(f"Fluxo Institucional - {nome}", color='white', fontsize=14)
    ax.grid(color='#333333', linestyle='--')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def enviar_dossie(msg, foto, botoes):
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': foto}
    data = {'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps({'inline_keyboard': botoes})}
    requests.post(url_foto, files=files, data=data)

import json

def executar():
    for ticker, info in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            preco = float(df['Close'].iloc[-1])
            vol_medio = float(df['Volume'].mean())
            ultimo_vol = float(df['Volume'].iloc[-1])
            vela_verde = df['Close'].iloc[-1] > df['Open'].iloc[-1]

            if ultimo_vol > (vol_medio * 1.3):
                direcao = "COMPRA (LONG)" if vela_verde else "VENDA (SHORT)"
                tp = round(preco * (1.01 if vela_verde else 0.99), 2)
                sl = round(preco * (0.995 if vela_verde else 1.005), 2)

                # Registrar na planilha automático (Auditoria do Bot)
                requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={info['nome']}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")

                # Preparar Mensagem e Botões
                msg = (f"🚨 **DOSSIÊ {direcao}**\n\n"
                       f"💎 **Ativo:** {info['nome']}\n"
                       f"💰 **Preço:** {preco}\n"
                       f"🎯 **Alvo:** {tp}\n"
                       f"🛑 **Stop:** {sl}\n\n"
                       f"👇 Gilney, você entrou nessa?")
                
                link_posicionado = f"{WEBAPP_URL}?acao=posicionado&ativo={info['nome']}"
                botoes = [[{"text": "✅ Estou Posicionado", "url": link_posicionado}],
                          [{"text": "❌ Não Entrei", "url": "https://t.me/"}]]
                
                foto = gerar_grafico_dark(ticker, info['nome'])
                enviar_dossie(msg, foto, botoes)
        except Exception as e: print(f"Erro: {e}")

if __name__ == "__main__":
    executar()
