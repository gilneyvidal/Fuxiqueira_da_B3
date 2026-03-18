import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import io
import json

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Ativos para o teste
ATIVOS = {
    "BTC-USD": {"nome": "Bitcoin (TESTE)", "tp_perc": 0.02, "sl_perc": 0.01}
}

def gerar_grafico_dark(ticker, nome):
    plt.style.use('dark_background')
    data = yf.download(ticker, period="1d", interval="15m", progress=False)
    if data.empty: return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(data.index, data['Close'], color='#00ff88', linewidth=2)
    ax.fill_between(data.index, data['Close'], color='#00ff88', alpha=0.1)
    ax.set_title(f"TESTE DE CONEXÃO - {nome}", color='white', fontsize=14)
    ax.grid(color='#333333', linestyle='--')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

def enviar_dossie(msg, foto, botoes):
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto, 'image/png')}
    payload = {
        'chat_id': CHAT_ID, 
        'caption': msg, 
        'parse_mode': 'Markdown', 
        'reply_markup': json.dumps({'inline_keyboard': botoes})
    }
    r = requests.post(url_foto, files=files, data=payload)
    print(f"Status Telegram: {r.status_code}")

def executar():
    print(f"🚀 EXECUTANDO TESTE DE SISTEMA...")
    for ticker, info in ATIVOS.items():
        try:
            df = yf.download(ticker, period="1d", interval="15m", progress=False)
            preco = float(df['Close'].iloc[-1])
            
            # FORÇANDO O SINAL (Ignorando o filtro de volume apenas para teste)
            direcao = "TESTE DE COMPRA"
            tp = round(preco * 1.02, 2)
            sl = round(preco * 0.99, 2)

            # 1. Tentar registrar na planilha
            print("Enviando para a Planilha...")
            r_sheet = requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={info['nome']}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")
            print(f"Status Planilha: {r_sheet.status_code}")

            # 2. Enviar Dossiê com Gráfico
            msg = (f"🛠️ **TESTE DE SISTEMA - TUDO OK!**\n\n"
                   f"💎 **Ativo:** {info['nome']}\n"
                   f"💰 **Preço:** {preco}\n"
                   f"🎯 **Alvo:** {tp}\n"
                   f"🛑 **Stop:** {sl}\n\n"
                   f"Se você recebeu esta foto e a planilha preencheu, o robô está pronto para a noite!")
            
            link_posicionado = f"{WEBAPP_URL}?acao=posicionado&ativo={info['nome']}"
            botoes = [[{"text": "✅ ESTOU POSICIONADO", "url": link_posicionado}]]
            
            foto = gerar_grafico_dark(ticker, info['nome'])
            if foto:
                enviar_dossie(msg, foto, botoes)
        except Exception as e:
            print(f"Erro no teste: {e}")

if __name__ == "__main__":
    executar()
