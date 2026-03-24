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

def gerar_grafico_profissional(df, nome, tp, sl, entrada):
    # Cores Institucionais
    mc = mpf.make_marketcolors(up='#00ff88', down='#ff3355', inherit=True)
    # Removi o 'edge' daqui que era o culpado pelo erro
    s  = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, gridcolor='#333333', facecolor='black')
    
    # Linhas de Alvo, Stop e Entrada
    hlines_config = dict(hlines=[tp, sl, entrada], 
                         colors=['#00ff00', '#ff0000', '#0088ff'], 
                         linestyle=['-', '-', '--'], 
                         linewidths=[1.5, 1.5, 1.0])

    buf = io.BytesIO()
    
    # Plotando os últimos 40 candles M15
    mpf.plot(df, type='candle', style=s, 
             title=f"\n[SINAL TESTE] {nome}",
             ylabel='Preco',
             hlines=hlines_config,
             savefig=dict(fname=buf, format='png', bbox_inches='tight'),
             figsize=(10, 6))
    
    buf.seek(0)
    return buf

def testar_audacia():
    ticker = "GC=F" # Ouro
    nome = "OURO (TESTE)"
    
    print(f"Buscando dados para {ticker}...")
    df = yf.download(ticker, period="3d", interval="15m", progress=False)
    
    if df.empty:
        print("Erro nos dados.")
        return

    # Pega o último preço fechado com segurança
    fechamentos = df['Close'].values.flatten()
    entrada = round(float(fechamentos[-1]), 2)
    
    # Setup 2:1
    sl = round(entrada - 10.00, 2)
    tp = round(entrada + 20.00, 2)
    
    print(f"Sucesso nos dados! Entrada: {entrada} | Alvo: {tp} | Stop: {sl}")

    msg = (f"🚨 **[TESTE VISUAL FINAL]** 🚨\n\n"
           f"💎 **Ativo:** {nome}\n"
           f"💰 **Entrada:** {entrada}\n"
           f"🎯 **Alvo:** {tp}\n"
           f"🛑 **Stop:** {sl}\n\n"
           f"Se a foto chegou, o Sentinela está PRONTO! ✅")
    
    foto = gerar_grafico_profissional(df.tail(40), nome, tp, sl, entrada)
    
    # Envio pro Telegram
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                  files={'photo': foto}, 
                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown'})
    
    print("Sinal enviado!")

if __name__ == "__main__":
    testar_audacia()
