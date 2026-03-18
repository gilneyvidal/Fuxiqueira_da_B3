import os
import requests
import pandas as pd
import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf
import io

# --- CONFIGURAÇÕES DE ACESSO (100% PROTEGIDAS) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
MEU_ID = os.getenv("TELEGRAM_CHAT_ID")
ID_MAE = os.getenv("TELEGRAM_ID_MAE")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Lista de transmissão familiar
IDS_FAMILIA = [id for id in [MEU_ID, ID_MAE] if id]

ATIVOS = {
    "GC=F": "Ouro", "SI=F": "Prata", "HG=F": "Cobre",
    "CL=F": "Petróleo", "BTC-USD": "Bitcoin", "^GSPC": "S&P 500"
}

def get_brasilia_time():
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime('%H:%M')

def gerar_grafico_dark(ticker, nome, data):
    df = data.tail(20)
    mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, facecolor='#121212', edgecolor='#444')
    buf = io.BytesIO()
    mpf.plot(df, type='candle', style=s, title=f"\nSMC: {nome}", savefig=buf)
    buf.seek(0)
    return buf

def enviar_dossie(nome, preco, tipo, tp, sl, grafico):
    hora = get_brasilia_time()
    emoji = "📈 COMPRA" if tipo == "COMPRA" else "📉 VENDA"
    msg = (f"🚨 **{emoji}**\n📊 **Ativo:** {nome}\n💰 **Entrada:** {preco}\n🎯 **Alvo:** {tp}\n🛑 **Stop:** {sl}\n🕒 {hora}")
    
    link_confirmar = f"{WEBAPP_URL}?acao=entrada&ativo={nome}&preco={preco}&tp={tp}&sl={sl}"
    botoes = {"inline_keyboard": [[{"text": "✅ ESTOU POSICIONADO", "url": link_confirmar}]]}

    for chat_id in IDS_FAMILIA:
        url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        grafico.seek(0)
        requests.post(url_foto, data={'chat_id': chat_id, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': str(botoes).replace("'", '"')}, files={'photo': grafico})

def analisar_mercado():
    for ticker, nome in ATIVOS.items():
        try:
            data = yf.download(ticker, period="2d", interval="15m", progress=False)
            if data.empty: continue
            
            ultimo = data.iloc[-1]
            vol_medio = data['Volume'].mean()
            preco = round(float(ultimo['Close']), 2)
            
            # --- FILTRO DE ELITE (40% acima da média) ---
            if ultimo['Volume'] > (vol_medio * 1.4):
                tipo = "COMPRA" if ultimo['Close'] > ultimo['Open'] else "VENDA"
                tp = round(preco * 1.015, 2) if tipo == "COMPRA" else round(preco * 0.985, 2)
                sl = round(preco * 0.993, 2) if tipo == "COMPRA" else round(preco * 1.007, 2)
                
                # Registro automático na planilha para auditoria
                requests.get(f"{WEBAPP_URL}?acao=entrada&ativo={nome}&preco={preco}&tp={tp}&sl={sl}")
                
                grafico = gerar_grafico_dark(ticker, nome, data)
                enviar_dossie(nome, preco, tipo, tp, sl, grafico)
        except Exception as e:
            print(f"Erro em {nome}: {e}")

if __name__ == "__main__":
    analisar_mercado()
