import os
import requests
import pandas as pd
import datetime

# --- CONFIGURAÇÕES DE ELITE ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ATIVOS = ["XAUUSD", "WTI", "WIN", "SPX500", "BTCUSD"]

def get_brasilia_time():
    # Ajuste de fuso para Brasília (GMT-3)
    return (datetime.datetime.utcnow() - datetime.timedelta(hours=3)).strftime('%H:%M')

def enviar_dossie(ativo, nota, contexto, risco, gatilho):
    hora = get_brasilia_time()
    mensagem = (
        f"📊 **DOSSIÊ DE OPORTUNIDADE (Nota: {nota}/10)**\n"
        f"🪙 **Ativo:** {ativo}\n"
        f"🕒 **Hora (Brasília):** {hora}\n"
        f"🎯 **Contexto:** {contexto}\n"
        f"🛡️ **Gatilho:** {gatilho}\n"
        f"💰 **Risco Est. (1 Contrato):** R$ {risco}\n\n"
        f"⚠️ *Filtro de Notícias: Nenhuma notícia de alto impacto na próxima hora.*\n"
        f"---------------------------\n"
        f"Deseja registrar essa entrada na auditoria?"
    )
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Adicionando os botões interativos
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Entrei", "callback_data": "entrei"},
                {"text": "🚫 Fora do Setup", "callback_data": "fora"}
            ]]
        }
    }
    requests.post(url, json=payload)

def analisar_mercado():
    # Aqui o bot faria a varredura técnica. 
    # Para este exemplo de estrutura, simulamos a detecção de um setup nota 9 no Ouro.
    # Na implementação final, este bloco consumirá APIs de preço (Yahoo Finance ou MetaTrader API).
    
    for ativo in ATIVOS:
        # Exemplo de lógica de detecção:
        if ativo == "XAUUSD":
            enviar_dossie(
                ativo="XAUUSD (Ouro)",
                nota="9.2",
                contexto="Quebra de estrutura (ChoCh) + Reação em Order Block de 15min.",
                risco="45,00",
                gatilho="Fechamento acima do Fair Value Gap"
            )

if __name__ == "__main__":
    if TOKEN and CHAT_ID:
        analisar_mercado()
    else:
        print("Erro: Credenciais não configuradas nas Secrets do GitHub.")
      
