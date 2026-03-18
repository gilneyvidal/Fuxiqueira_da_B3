import os
import requests
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import io
import json

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
# Lembre-se de atualizar esta SECRET no GitHub com o ID do Grupo (ex: -100...)
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") 
WEBAPP_URL = os.getenv("WEBAPP_URL")

# Watchlist de Elite (Commodities, Metais e Índices)
ATIVOS = {
    "GC=F": {"nome": "Ouro", "tp_perc": 0.01, "sl_perc": 0.005, "dec": 2},
    "SI=F": {"nome": "Prata", "tp_perc": 0.015, "sl_perc": 0.008, "dec": 3},
    "HG=F": {"nome": "Cobre", "tp_perc": 0.012, "sl_perc": 0.006, "dec": 4},
    "REMX": {"nome": "Terras Raras", "tp_perc": 0.02, "sl_perc": 0.01, "dec": 2},
    "BTC-USD": {"nome": "Bitcoin", "tp_perc": 0.02, "sl_perc": 0.01, "dec": 2},
    "^GSPC": {"nome": "S&P 500", "tp_perc": 0.006, "sl_perc": 0.003, "dec": 2}
}

def gerar_grafico_dark(ticker, nome):
    try:
        plt.style.use('dark_background')
        # MELHORIA: period="5d" para dar contexto semanal ao trade de hoje
        data = yf.download(ticker, period="5d", interval="15m", progress=False)
        if data.empty: return None
        
        # Correção técnica: Achata os dados para 1D
        precos = data['Close'].values.flatten() 
        tempos = data.index
        
        fig, ax = plt.subplots(figsize=(10, 5))
        # Cor Neon para destacar no fundo escuro
        ax.plot(tempos, precos, color='#00ff88', linewidth=2) 
        ax.fill_between(tempos, precos, color='#00ff88', alpha=0.1)
        
        ax.set_title(f"Fluxo Institucional Semanal - {nome}", color='white', fontsize=14)
        ax.grid(color='#333333', linestyle='--')
        
        # Formatação do eixo X para não ficar bagunçado
        fig.autofmt_xdate()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
    except: return None

def enviar_dossie(msg, foto, botoes):
    # Envia para o CHAT_ID que agora deve ser o do GRUPO
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
    print(f"🕵️‍♂️ Sentinela v2.0 Iniciado. Varrendo o mercado para o grupo...")
    for ticker, info in ATIVOS.items():
        try:
            df = yf.download(ticker, period="2d", interval="15m", progress=False)
            if df.empty: continue
            
            ultimo_registro = df.iloc[-1]
            
            # Tratamento de erro de dados e MELHORIA: Arredondamento (round)
            raw_preco = float(ultimo_registro['Close'].iloc[0]) if isinstance(ultimo_registro['Close'], pd.Series) else float(ultimo_registro['Close'])
            preco = round(raw_preco, info['dec'])
            
            raw_abertura = float(ultimo_registro['Open'].iloc[0]) if isinstance(ultimo_registro['Open'], pd.Series) else float(ultimo_registro['Open'])
            
            vol_medio = float(df['Volume'].mean())
            ultimo_vol = float(ultimo_registro['Volume'])
            vela_verde = raw_preco > raw_abertura

            # REGRA DE OURO SMC: Volume 30% acima da média
            if ultimo_vol > (vol_medio * 1.3):
                direcao = "COMPRA (LONG)" if vela_verde else "VENDA (SHORT)"
                
                # Cálculo de TP/SL com arredondamento preciso
                raw_tp = preco * (1 + info['tp_perc']) if vela_verde else preco * (1 - info['tp_perc'])
                raw_sl = preco * (1 - info['sl_perc']) if vela_verde else preco * (1 + info['sl_perc'])
                tp = round(raw_tp, info['dec'])
                sl = round(raw_sl, info['dec'])

                # 1. Registrar Auditoria na Planilha
                requests.get(f"{WEBAPP_URL}?acao=sinal&ativo={info['nome']}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}")

                # 2. Mensagem e Botões Personalizados para o Grupo
                msg = (f"🚨 **DOSSIÊ {direcao}**\n\n"
                       f"💎 **Ativo:** {info['nome']}\n"
                       f"💰 **Preço de Entrada:** {preco}\n"
                       f"🎯 **Alvo (Take Profit):** {tp}\n"
                       f"🛑 **Stop (Stop Loss):** {sl}\n\n"
                       f"👇 Quem da família Fuxiqueira entrou nessa?")
                
                link_gilney = f"{WEBAPP_URL}?acao=posicionado&ativo={info['nome']}&quem=Gilney"
                link_elisete = f"{WEBAPP_URL}?acao=posicionado&ativo={info['nome']}&quem=Elisete"
                
                botoes = [
                    [{"text": "🙋‍♂️ Gilney Entrou", "url": link_gilney}],
                    [{"text": "🙋‍♀️ Elisete Entrou", "url": link_elisete}],
                    [{"text": "❌ Ninguém Entrou", "url": "https://t.me/"}]
                ]
                
                # Gera o gráfico com contexto de 5 dias
                foto = gerar_grafico_dark(ticker, info['nome'])
                if foto: enviar_dossie(msg, foto, botoes)
                print(f"✅ Sinal enviado para o grupo: {info['nome']}")
                
        except Exception as e:
            print(f"Erro em {ticker}: {e}")

if __name__ == "__main__":
    executar()
