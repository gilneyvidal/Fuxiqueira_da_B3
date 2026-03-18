import os
import requests
import pandas as pd
import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf
import io

# --- ACESSO PROTEGIDO ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
ID_GILNEY = os.getenv("TELEGRAM_CHAT_ID")
ID_ELISETE = os.getenv("TELEGRAM_ID_MAE")
WEBAPP_URL = os.getenv("WEBAPP_URL")

IDS_FAMILIA = {"Gilney": ID_GILNEY, "Elisete": ID_ELISETE}

ATIVOS = {
    "GC=F": "Ouro", "SI=F": "Prata", "HG=F": "Cobre",
    "CL=F": "Petróleo", "BTC-USD": "Bitcoin", "^GSPC": "S&P 500"
}

def get_preco_atual(ticker):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        return float(data['Close'].iloc[-1]) if not data.empty else None
    except: return None

def enviar_telegram(msg, chat_id, grafico=None, botoes=None):
    url_base = f"https://api.telegram.org/bot{TOKEN}/"
    if grafico:
        url = url_base + "sendPhoto"
        grafico.seek(0)
        requests.post(url, data={'chat_id': chat_id, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': str(botoes).replace("'", '"')}, files={'photo': grafico})
    else:
        url = url_base + "sendMessage"
        requests.post(url, data={'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'})

def gerenciar_auditoria():
    """Vigia a planilha e avisa se as metas foram atingidas"""
    try:
        r = requests.get(f"{WEBAPP_URL}?acao=get_abertos")
        ordens = r.json()
        for o in ordens:
            ticker = [k for k, v in ATIVOS.items() if v == o['ativo']][0]
            atual = get_preco_atual(ticker)
            if not atual: continue

            resultado = ""
            if o['tipo'] == "COMPRA":
                if atual >= float(o['tp']): resultado = "TAKE PROFIT (LUCRO) 💰"
                elif atual <= float(o['sl']): resultado = "STOP LOSS (PREJUÍZO) 🛑"
            else:
                if atual <= float(o['tp']): resultado = "TAKE PROFIT (LUCRO) 💰"
                elif atual >= float(o['sl']): resultado = "STOP LOSS (PREJUÍZO) 🛑"

            if resultado:
                requests.get(f"{WEBAPP_URL}?acao=fechar&linha={o['linha']}&resultado={resultado}")
                for nome, cid in IDS_FAMILIA.items():
                    enviar_telegram(f"🏁 **AUDITORIA: {o['ativo']} ENCERRADO**\nResultado: {resultado}\nPreço: {atual}", cid)
    except: pass

def analisar_mercado():
    for ticker, nome in ATIVOS.items():
        try:
            data = yf.download(ticker, period="2d", interval="15m", progress=False)
            if data.empty: continue
            ultimo = data.iloc[-1]
            vol_medio = data['Volume'].mean()
            preco = round(float(ultimo['Close']), 2)

            if ultimo['Volume'] > (vol_medio * 1.4):
                tipo = "COMPRA" if ultimo['Close'] > ultimo['Open'] else "VENDA"
                tp = round(preco * 1.015, 2) if tipo == "COMPRA" else round(preco * 0.985, 2)
                sl = round(preco * 0.993, 2) if tipo == "COMPRA" else round(preco * 1.007, 2)
                
                # Registro automático para auditoria de 100% dos sinais
                requests.get(f"{WEBAPP_URL}?acao=entrada&ativo={nome}&tipo={tipo}&preco={preco}&tp={tp}&sl={sl}")
                
                # Gerar Gráfico Dark Mode
                df_plot = data.tail(20)
                mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000', inherit=True)
                s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, facecolor='#121212', edgecolor='#444')
                buf = io.BytesIO()
                mpf.plot(df_plot, type='candle', style=s, title=f"\nSMC: {nome}", savefig=buf)
                
                for user_nome, cid in IDS_FAMILIA.items():
                    link = f"{WEBAPP_URL}?acao=posicionamento&user={user_nome}&ativo={nome}"
                    botoes = {"inline_keyboard": [[{"text": f"✅ {user_nome}: Entrei", "url": link}]]}
                    msg = f"🚨 **SINAL DE {tipo}**\n📊 **{nome}**\n💰 Entrada: {preco}\n🎯 Alvo: {tp}\n🛑 Stop: {sl}"
                    enviar_telegram(msg, cid, grafico=buf, botoes=botoes)
        except: pass

if __name__ == "__main__":
    gerenciar_auditoria()
    analisar_mercado()
