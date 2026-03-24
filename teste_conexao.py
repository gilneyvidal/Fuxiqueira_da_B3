import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import io
import json

# --- CONFIGS (Pega das Secrets do GitHub) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def gerar_grafico_profissional(df, nome, tp, sl, entrada):
    # Configuração visual do gráfico (Dark Mode e Estilo de Velas)
    mc = mpf.make_marketcolors(up='#00ff88', down='#ff3355', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc, edge='black', gridcolor='#333333', facecolor='black')
    
    # Adicionando as linhas de Alvo, Stop e Entrada (HPs)
    hlines_config = dict(hlines=[tp, sl, entrada], 
                         colors=['#00ff00', '#ff0000', '#0088ff'], 
                         linestyle=['-', '-', '--'], 
                         linewidths=[1.5, 1.5, 1.0])

    buf = io.BytesIO()
    
    # Plotando o gráfico de Candles M15
    mpf.plot(df, type='candle', style=s, 
             title=f"\n[TESTE AUDACIOSO] {nome} (M15)",
             ylabel='Preço',
             hlines=hlines_config,
             savefig=dict(fname=buf, format='png', bbox_inches='tight'),
             figsize=(10, 6))
    
    buf.seek(0)
    return buf

def testar_audacia():
    # ATIVO AUDACIOSO: Ouro (GC=F)
    ticker = "GC=F"
    nome = "Ouro (TESTE)"
    
    print(f"Buscando dados para {ticker}...")
    df = yf.download(ticker, period="3d", interval="15m", progress=False)
    
    if df.empty:
        print("Erro: Não foi possível pegar dados históricos.")
        return

    # --- AJUSTE CIRÚRGICO AQUI ---
    # Pegamos apenas a coluna 'Close' e o último valor de forma garantida
    ultimo_fechamento = df['Close'].values[-1]
    
    # Se o yfinance retornar um array (tabela), pegamos o primeiro item
    if hasattr(ultimo_fechamento, "__len__"):
        entrada = round(float(ultimo_fechamento[0]), 2)
    else:
        entrada = round(float(ultimo_fechamento), 2)
    
    # Configuração do trade fake (2:1)
    sl = round(entrada - 10.00, 2)
    tp = round(entrada + 20.00, 2)
    
    print(f"Sucesso! Entrada: {entrada} | Alvo: {tp} | Stop: {sl}")

    msg = (f"🚨 **🚨 [TESTE AUDACIOSO - FUXIQUEIRA] 🚨** 🚨\n"
           f"Se você está vendo isso, o gráfico de Candles funcionou!\n\n"
           f"💎 **Ativo:** {nome}\n"
           f"💰 **Preço de Entrada:** {entrada}\n"
           f"🎯 **Alvo:** {tp}\n"
           f"🛑 **Stop:** {sl}\n\n"
           f"O visual ficou do jeito que você queria?")
    
    botoes = {"inline_keyboard": [
        [{"text": "🔥 FICOU TOP", "url": "https://t.me/BotFather"}],
        [{"text": "🛠️ PRECISA AJUSTAR", "url": "https://t.me/BotFather"}]
    ]}
    
    # Gera o gráfico com as 40 últimas velas
    foto = gerar_grafico_profissional(df.tail(40), nome, tp, sl, entrada)
    
    # Envio pro Telegram
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                  files={'photo': foto}, 
                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
    
    print("Sinal enviado com sucesso!")

if __name__ == "__main__":
    testar_audacia()
