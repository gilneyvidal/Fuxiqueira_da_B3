import os
import requests
import pandas as pd
import yfinance as yf
import datetime

# --- CONFIGURAÇÕES DE ACESSO ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ativos Globais (Ouro, Petróleo WTI, BTC, S&P 500)
# Para o Mini Índice (WIN), como o Yahoo Finance tem atraso, focaremos na análise técnica global que dita o WIN.
ATIVOS = {
    "XAUUSD=F": "Ouro (Gold)",
    "CL=F": "Petróleo WTI",
    "BTC-USD": "Bitcoin",
    "^GSPC": "S&P 500"
}

def get_brasilia_time():
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime('%H:%M')

def analisar_smc(ticker):
    """
    Simulação de lógica SMC: Identifica se o preço está em zona de 
    Desequilíbrio (FVG) ou Order Block baseado nas últimas velas.
    """
    data = yf.download(ticker, period="1d", interval="15m", progress=False)
    if data.empty: return None
    
    last_candles = data.tail(5)
    preco_atual = last_candles['Close'].iloc[-1]
    
    # Lógica simplificada de Order Block / FVG para o bot
    # (Se a última vela teve volume 20% acima da média e fechou forte)
    vol_medio = data['Volume'].mean()
    ultimo_vol = last_candles['Volume'].iloc[-1]
    
    if ultimo_vol > vol_medio * 1.2:
        contexto = "Forte presença institucional (Volume 20% acima da média)"
        nota = "8.5"
        risco = "Técnico (Abaixo do pavio da vela anterior)"
        return {
            "preco": round(preco_atual, 2),
            "contexto": contexto,
            "nota": nota,
            "risco": risco
        }
    return None

def enviar_telegram(ativo_nome, analise):
    hora = get_brasilia_time()
    msg = (
        f"📊 **DOSSIÊ SMC: {ativo_nome}**\n"
        f"🕒 **Brasília:** {hora}\n"
        f"💰 **Preço Atual:** {analise['preco']}\n"
        f"🎯 **Nota:** {analise['nota']}/10\n"
        f"🧠 **Contexto:** {analise['contexto']}\n"
        f"🛡️ **Risco:** {analise['risco']}\n\n"
        f"🔘 `[✅ Entrei]` | `[🚫 Fora]`"
    )
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID, 
        "text": msg, 
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Registrar Entrada", "url": f"https://github.com/{os.getenv('GITHUB_REPOSITORY')}/edit/main/DIARIO_DE_TRADE.md"}
            ]]
        }
    }
    requests.post(url, json=payload)

def executar_varredura():
    print(f"Iniciando varredura institucional às {get_brasilia_time()}...")
    for ticker, nome in ATIVOS.items():
        resultado = analisar_smc(ticker)
        if resultado:
            enviar_telegram(nome, resultado)
            print(f"Alerta enviado para {nome}")

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("Erro: Secrets TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não encontradas.")
    else:
        executar_varredura()
        
