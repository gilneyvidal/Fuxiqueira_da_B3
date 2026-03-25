# 🛡️ Projeto Sentinela SMC - Fuxiqueira da B3

> *"Onde a gente chegou, viu? Do sonho à realidade."* — **Progresso e Vitória.**

Este projeto é um sistema de monitoramento inteligente baseado em **Smart Money Concepts (SMC)**, focado em identificar o rastro dos grandes players (tubarões) através de anomalias de volume e fluxo institucional.

---

## 🚀 Visão do Projeto
O objetivo é automatizar a análise técnica de ativos globais, fornecendo sinais de alta precisão via Telegram, permitindo que o operador foque na gestão de risco e na execução, sem precisar ficar "preso" na frente do gráfico 24h por dia. Cada lucro é um tijolo a mais no sonho do outdoor da Monique e no crescimento da Vidal Design Solutions.

## 🧠 Lógica Operacional
- **Intervalo de Tempo:** 15 Minutos (M15).
- **Filtro de Volume (Régua):** 1.3x (O sinal só dispara se o volume for 30% maior que a média).
- **Gerenciamento de Risco:** 2 para 1 (Busca o dobro do que aceita perder).
- **Stop Loss Padrão:** 0.5% do preço de entrada (ajustável conforme a volatilidade).

## 📊 Dicionário de Busca (Plataforma)
O robô monitora via Yahoo Finance, mas entrega o código pronto para sua plataforma de trade:

| Ativo | Código Interno | **Busca no Telegram** |
| :--- | :--- | :--- |
| **Nasdaq 100** | `NQ=F` | **USTEC** |
| **Ouro** | `GC=F` | **XAUUSD** |
| **S&P 500** | `^GSPC` | **US500** |
| **Petróleo** | `CL=F` | **WTI** |
| **Prata** | `SI=F` | **XAGUSD** |
| **Bitcoin** | `BTC-USD` | **BTCUSD** |
| **Ethereum** | `ETH-USD` | **ETHUSD** |
| **Euro/Dólar** | `EURUSD=X` | **EURUSD** |

## ⏱️ Realidade do Delay
O sistema opera via GitHub Actions com ciclos a cada 15-20 minutos.
- **Deley Estimado:** 1 a 3 minutos entre o fechamento da vela e o alerta.
- **Ação:** Se o preço já correu muito no momento do alerta, evite a entrada "atrasada".

## 🛠️ Tecnologias
- **Python:** Lógica SMC e análise.
- **mplfinance:** Gráficos de candles profissionais.
- **GitHub Actions:** Execução em nuvem 24/7.
- **Telegram Bot:** Interface de alerta em tempo real.

---
**"Mente no lugar e foco no objetivo."**

