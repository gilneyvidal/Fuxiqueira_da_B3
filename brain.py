import os
import requests
import pandas as pd
import yfinance as yf
import datetime

# --- CONFIGURAÇÕES DE ACESSO ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Tickers estáveis para o Yahoo Finance
ATIVOS = {
    "GC=F": "Ouro (Gold)",
    "CL=F": "Petróleo WTI",
    "BTC-USD": "Bitcoin",
    "^GSPC": "S&P 500"
}

def get_brasilia_time():
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime('%H:%M')

def analisar_smc(ticker):
    try:
        # Baixa os últimos 2 dias para ter média de volume
        data = yf.download(ticker, period="2d", interval="15m", progress=False)
        
        if data.empty:
            return None
        
        # Corrigindo o erro de "ambiguidade" forçando valores numéricos puros
        # Pegamos apenas a coluna 'Close' e 'Volume'
        precos = data['Close']
        volumes = data['Volume']
        
        # Pegamos o ÚLTIMO valor disponível (scalar)
        preco_atual = float(precos.iloc[-1])
        vol_medio = float(volumes.mean())
        ultimo_vol = float(volumes.iloc[-1])
        
        # Lógica Institucional: Volume 10% acima da média
        if ultimo_vol > (vol_medio * 1.1):
            return {
                "preco": round(preco_atual, 2),
                "contexto": "Volume Institucional detectado na zona",
                "nota": "9.0",
                "risco": "Stop técnico abaixo do pavio da vela"
            }
    except Exception as e:
        print(f"Erro técnico no ativo {ticker}: {e}")
        return None
    return None

def enviar_telegram(ativo_nome, analise):
    hora = get_brasilia_time()
    msg = (
        f"📊 **DOSSIÊ SMC: {ativo_nome}**\n"
        f"🕒 **Brasília:** {hora}\n"
        f"💰 **Preço:** {analise['preco']}\n"
        f"🎯 **Nota:** {analise['nota']}/10\n"
        f"🧠 **Contexto:** {analise['contexto']}\n"
        f"🛡️ **Risco:** {analise['risco']}\n\n"
        f"🔘 `[✅ Entrei]` | `[🚫 Fora]`"
    )
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def executar_varredura():
    print(f"Iniciando varredura às {get_brasilia_time()}...")
    for ticker, nome in ATIVOS.items():
        print(f"Analisando {nome}...")
        resultado = analisar_smc(ticker)
        if resultado:
            enviar_telegram(nome, resultado)
            print(f"Alerta enviado para {nome}!")

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("Erro: Credenciais (Secrets) não encontradas.")
    else:
        executar_varredura()
        
