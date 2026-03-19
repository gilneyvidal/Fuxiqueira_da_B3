import os
import requests
import json

# --- PEGA AS SUAS CONFIGURAÇÕES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBAPP_URL = os.getenv("WEBAPP_URL")

def testar_tudo():
    print("🚀 Iniciando teste de conexão...")
    
    # Dados de teste
    ativo = "TESTE-BTC"
    preco = 70000.00
    tp = 72000.00
    sl = 69000.00
    direcao = "COMPRA (TESTE)"

    # 1. TESTE DA PLANILHA
    print("📊 Tentando registrar na planilha...")
    url_planilha = f"{WEBAPP_URL}?acao=sinal&ativo={ativo}&direcao={direcao}&preco={preco}&tp={tp}&sl={sl}"
    r_planilha = requests.get(url_planilha)
    
    if r_planilha.text == "OK":
        print("✅ Planilha respondeu: SINAL REGISTRADO!")
    else:
        print(f"❌ Erro na planilha: {r_planilha.text}")
        return

    # 2. TESTE DO TELEGRAM
    print("📱 Enviando mensagem para o Telegram...")
    msg = f"🧪 **SINAL DE TESTE**\n💎 {ativo} | 💰 {preco}\n\n👇 Gilney, clica no seu botão para testar a confirmação!"
    
    botoes = {"inline_keyboard": [
        [{"text": "✅ Gilney Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={ativo}&quem=gilney"}],
        [{"text": "✅ Elisete Posicionado", "url": f"{WEBAPP_URL}?acao=confirmar&ativo={ativo}&quem=elisete"}]
    ]}
    
    url_tg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r_tg = requests.post(url_tg, data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown', 'reply_markup': json.dumps(botoes)})
    
    if r_tg.status_code == 200:
        print("✅ Telegram enviado com sucesso!")
    else:
        print(f"❌ Erro no Telegram: {r_tg.text}")

if __name__ == "__main__":
    testar_tudo()
