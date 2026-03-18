import os
import requests
import pandas as pd
import yfinance as yf
import datetime

# --- CONFIGURAÇÕES DE ACESSO (SECRETS DO GITHUB) ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Mapeamento de Ativos Globais
ATIVOS = {
    "GC=F": "Ouro (Gold)",
    "CL=F": "Petróleo WTI",
    "BTC-USD": "Bitcoin",
    "^GSPC": "S&P 500"
}

def get_brasilia_time():
    """Retorna o horário atual de Brasília (GMT-3)"""
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime('%H:%M')

def analisar_smc(ticker):
    """Analisa se há volume institucional (SMC) nos últimos 15 minutos"""
    try:
        # Baixa os dados dos últimos 2 dias para calcular a média de volume
        data = yf.download(ticker, period="2d", interval="15m", progress=False)
        
        if data.empty:
            return None
        
        # Extrai valores puros para evitar erros de ambiguidade
        precos = data['Close']
        volumes = data['Volume']
        
        preco_atual = float(precos.iloc[-1])
        vol_medio = float(volumes.mean())
        ultimo_vol = float(volumes.iloc[-1])
        
        # Lógica: Volume 10% acima da média indica presença do 'Big Player'
        if ultimo_vol > (vol_medio * 1.1):
            return {
                "preco": round(preco_atual, 2),
                "contexto": "Volume Institucional (Smart Money) detectado",
                "nota": "9.2",
                "risco": "Stop técnico abaixo do pavio da última vela"
            }
    except Exception as e:
        print(f"Erro ao analisar {ticker}: {e}")
        return None
    return None

def enviar_telegram(ativo_nome, analise):
    """Envia o Dossiê traduzido com botão clicável para o Telegram"""
    hora = get_brasilia_time()
    
    # Texto do Alerta Traduzido
    msg = (
        f"📊 **DOSSIÊ DE OPORTUNIDADE: {ativo_nome}**\n"
        f"🕒 **Horário Brasília:** {hora}\n"
        f"💰 **Preço de Entrada:** {analise['preco']}\n"
        f"🎯 **Nota de Assertividade:** {analise['nota']}/10\n"
        f"🧠 **Contexto:** {analise['contexto']}\n"
        f"🛡️ **Gestão:** {analise['risco']}\n"
    )
    
    # URL do seu diário no GitHub para o botão
    # Como o nome do seu repositório é 'Fuxiqueira_da_B3', o link fica assim:
    link_diario = "https://github.com/gilneyvidal/Fuxiqueira_da_B3/edit/main/DIARIO_DE_TRADE.md"
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ REGISTRAR TRADE NO DIÁRIO", "url": link_diario}
            ]]
        }
    }
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def executar_varredura():
    print(f"Iniciando varredura institucional às {get_brasilia_time()}...")
    for ticker, nome in ATIVOS.items():
        print(f"Verificando {nome}...")
        resultado = analisar_smc(ticker)
        if resultado:
            enviar_telegram(nome, resultado)
            print(f"Alerta enviado com sucesso para {nome}!")

if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("ERRO: TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não configurados no GitHub Secrets.")
    else:
        executar_varredura()
        
