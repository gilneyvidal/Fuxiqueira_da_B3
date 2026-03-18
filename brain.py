import os
import requests
import pandas as pd
import yfinance as yf
import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf
import io

# --- CONFIGURAÇÕES DE ACESSO ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
MEU_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# 👵 ADICIONE O ID DA SUA MÃE AQUI ENTRE AS ASPAS:
ID_MAE = "6520050958" 

IDS_FAMILIA = [MEU_ID, ID_MAE]

# Ativos de Elite (Metais, Energia, Cripto e Índices)
# Alvos automáticos: TP (Lucro) 1.5% | SL (Stop) 0.7%
ATIVOS = {
    "GC=F": "Ouro", "SI=F": "Prata", "HG=F": "Cobre",
    "CL=F": "Petróleo", "BTC-USD": "Bitcoin", "^GSPC": "S&P 500"
}

def get_brasilia_time():
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime('%H:%M')

def gerar_grafico_dark(ticker, nome, data):
    """Gera um gráfico Dark Mode com as últimas 20 velas"""
    df = data.tail(20)
    mc = mpf.make_marketcolors(up='#00ff00', down='#ff0000', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, facecolor='#121212', edgecolor='#444')
    
    buf = io.BytesIO()
    mpf.plot(df, type='candle', style=s, title=f"\nSMC: {nome}", savefig=buf)
    buf.seek(0)
    return buf

def enviar_dossie(nome, preco, tipo, tp, sl, grafico):
    hora = get_brasilia_time()
    emoji = "📈 COMPRA (LONG)" if tipo == "COMPRA" else "📉 VENDA (SHORT)"
    
    msg = (
        f"🚨 **{emoji}**\n"
        f"📊 **Ativo:** {nome}\n"
        f"💰 **Entrada:** {preco}\n"
        f"🎯 **Alvo (TP):** {tp}\n"
        f"🛑 **Stop (SL):** {sl}\n"
        f"🕒 **Brasília:** {hora}"
    )
    
    # Link da Planilha para o botão (Manda pra sua WEBAPP_URL)
    link_confirmar = f"{WEBAPP_URL}?acao=entrada&ativo={nome}&preco={preco}&tp={tp}&sl={sl}"
    botoes = {"inline_keyboard": [[{"text": "✅ ESTOU POSICIONADO", "url": link_confirmar}]]}

    for chat_id in IDS_FAMILIA:
        if not chat_id: continue
        # Envia a foto do gráfico
        url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        files = {'photo': grafico}
        requests.post(url_foto, data={'chat_id': chat_id, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': str(botoes).replace("'", '"')}, files=files)
        grafico.seek(0) # Reseta o buffer para o próximo envio

def analisar_mercado():
    for ticker, nome in ATIVOS.items():
        try:
            data = yf.download(ticker, period="2d", interval="15m", progress=False)
            if data.empty: continue
            
            ultimo_candle = data.iloc[-1]
            penultimo_candle = data.iloc[-2]
            vol_medio = data['Volume'].mean()
            
            preco = round(float(ultimo_candle['Close']), 2)
            volume = float(ultimo_candle['Volume'])
            
            # Lógica SMC: Volume 40% acima da média (Rastro forte)
            if volume > (vol_medio * 1.4):
                # Se fechar acima da abertura = COMPRA | Se fechar abaixo = VENDA
                tipo = "COMPRA" if ultimo_candle['Close'] > ultimo_candle['Open'] else "VENDA"
                
                # Alvos automáticos (2 pra 1)
                tp = round(preco * 1.015, 2) if tipo == "COMPRA" else round(preco * 0.985, 2)
                sl = round(preco * 0.993, 2) if tipo == "COMPRA" else round(preco * 1.007, 2)
                
                # Registrar na planilha automaticamente (Auditoria de 100% dos sinais)
                requests.get(f"{WEBAPP_URL}?acao=entrada&ativo={nome}&preco={preco}&tp={tp}&sl={sl}")
                
                # Gerar gráfico e enviar
                grafico = gerar_grafico_dark(ticker, nome, data)
                enviar_dossie(nome, preco, tipo, tp, sl, grafico)
                print(f"✅ Dossiê enviado para {nome}")
                
        except Exception as e:
            print(f"Erro em {nome}: {e}")

if __name__ == "__main__":
    analisar_mercado()
