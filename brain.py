import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import io
import json

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Watchlist de Elite (Commodities, Metais e Índices)
ATIVOS = {
    "GC=F": {"nome": "Ouro", "tp_perc": 0.01, "sl_perc": 0.005},
    "SI=F": {"nome": "Prata", "tp_perc": 0.015, "sl_perc": 0.008},
    "HG=F": {"nome": "Cobre", "tp_perc": 0.012, "sl_perc": 0.006},
    "REMX": {"nome": "Terras Raras", "tp_perc": 0.02, "sl_perc": 0.01},
    "BTC-USD": {"nome": "Bitcoin", "tp_perc": 0.02, "sl_perc": 0.01},
    "^GSPC": {"nome": "S&P 500", "tp_perc": 0.006, "sl_perc": 0.003}
}

def gerar_grafico_dark(ticker, nome):
    try:
        plt.style.use('dark_background')
        data = yf.download(ticker, period="1d", interval="15m", progress=False)
        if data.empty: return None
        
        # Correção técnica: Achata os dados para 1D para evitar erro 'y1'
        precos = data['Close'].values.flatten() 
        tempos = data.index
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(tempos, precos, color='#00ff88', linewidth=2)
        ax.fill_between(tempos, precos, color='#00ff88', alpha=0.1)
        ax.set_title(f"Fluxo Institucional - {nome}", color='white', fontsize=14)
        ax.grid(color='#333333', linestyle='--')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
    except: return None

def enviar_dossie(msg, foto, botoes):
    url_foto = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    files = {'photo': ('graph.png', foto, 'image/png')}
    payload = {
        'chat_id': CHAT_ID, 
        'caption': msg, 
        'parse_mode': 'Markdown', 
        'reply_markup': json.dumps({'inline_keyboard': botoes})
    }
    requests.post(url_foto, files=files, data=payload)

def executar():
    print("🕵️‍♂️ Sentinela Iniciado. Varrendo o mercado em busca de Big Players...")
    for ticker, info in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            # Pega o último preço fechado (Tratamento para evitar erro de Series/Float)
            ultimo_registro = df.iloc[-1]
            preco = float(ultimo_registro['Close'].iloc[0]) if isinstance(ultimo_registro['Close'], pd.Series) else float(ultimo_registro['Close'])
            abertura = float(ultimo_registro['Open'].iloc[0]) if isinstance(ultimo_registro['Open'], pd.Series) else float(ultimo_registro['Open'])
            
            vol_medio = float(df['Volume'].mean())
            ultimo_vol = float(ultimo_registro['Volume'])
            vela_verde = preco > abertura

            # REGRA DE OURO: Volume 30% acima da média
            if ultimo_vol > (vol_medio * 1.3):
                direcao = "COMPRA (LONG)" if vela_verde else "VENDA (SHORT)"
                tp = round(preco * (1 + info['tp_perc']) if vela_verde else preco * (1 - info['tp_perc']), 2)
                sl = round(preco * (1 - info['sl_perc']) if vela_verde else preco * (1 + info['sl_perc']), 2)

                # 1. Registrar na planilha automático (Auditoria do Bot)
                requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={info['nome']}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")

                # 2. Mensagem e Botões
                msg = (f"🚨 **DOSSIÊ {direcao}**\n\n"
                       f"💎 **Ativo:** {info['nome']}\n"
                       f"💰 **Preço de Entrada:** {preco}\n"
                       f"🎯 **Alvo (Take Profit):** {tp}\n"
                       f"🛑 **Stop (Stop Loss):** {sl}\n\n"
                       f"👇 Gilney, você entrou nessa?")
                
                link_posicionado = f"{WEBAPP_URL}?acao=posicionado&ativo={info['nome']}"
                botoes = [[{"text": "✅ ESTOU POSICIONADO", "url": link_posicionado}]]
                
                foto = gerar_grafico_dark(ticker, info['nome'])
                if foto: enviar_dossie(msg, foto, botoes)
                print(f"✅ Sinal enviado para {info['nome']}")
                
        except Exception as e:
            print(f"Erro em {ticker}: {e}")

if __name__ == "__main__":
    executar()
