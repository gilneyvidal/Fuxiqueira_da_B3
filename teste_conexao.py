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
             title=f"\n[TESTE] Fluxo Institucional - {nome} (M15)",
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
    
    # Pega dados históricos recentes (mesmo com mercado fechado)
    df = yf.download(ticker, period="3d", interval="15m", progress=False)
    
    if df.empty:
        print("Erro: Não foi possível pegar dados históricos para o teste.")
        return

    # Pega o último preço fechado como entrada
    entrada = round(df['Close'].iloc[-1:].item(), 2)
    
    # Força uma entrada AUDACIOSA (Gerenciamento 2:1)
    # Stop de 10 pontos abaixo, Alvo de 20 pontos acima (exemplo rápido)
    sl = round(entrada - 10.00, 2)
    tp = round(entrada + 20.00, 2)
    
    print(f"Gerando sinal fake do Ouro: Entrada {entrada}, Alvo {tp}, Stop {sl}")

    # Monta a mensagem pro Telegram
    msg = (f"🚨 **🚨 [SINAL FAKE - TESTE VISUAL] 🚨** 🚨\n"
           f"Audácia ativada! Ignorando volume para testar o gráfico novo.\n\n"
           f"💎 **Ativo:** {nome}\n"
           f"💰 **Preço de Entrada:** {entrada}\n"
           f"🎯 **Alvo (2:1):** {tp}\n"
           f"🛑 **Stop Loss:** {sl}\n\n"
           f"👇 Aprovado o visual do novo dossiê?")
    
    # Botões Fake (sem URL real de confirmação, só pro layout)
    botoes = {"inline_keyboard": [
        [{"text": "✅ Layout Aprovado", "url": "https://telegram.org"}],
        [{"text": "❌ Precisa Ajustar", "url": "https://telegram.org"}]
    ]}
    
    # Gera o gráfico de candles com as linhas marcadas
    foto = gerar_grafico_profissional(df.tail(40), nome, tp, sl, entrada)
    
    # Manda pro Telegram
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto", 
                  files={'photo': foto}, 
                  data={'chat_id': CHAT_ID, 'caption': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
    
    print("Sinal Audacioso enviado pro Telegram!")

if __name__ == "__main__":
    testar_audacia()
