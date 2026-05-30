# crypto-pump-screener

**Crypto screener + Strategy Bot Académique**

Outil complet pour détecter les pumps sur Binance et tester tes stratégies en **paper trading** avec données réelles temps réel.

## 🚀 Nouvelles fonctionnalités (v1.0)

- **StrategyBot** : `/bot` - Dashboard moderne académique
- Analyse intelligente des paires USDC (même les plus obscures)
- Recommandation LONG/SHORT avec score de confiance + raisons stratégiques
- Graphiques interactifs (candlesticks 5m, heatmap de corrélation BTC/ETH)
- Paper Trading en direct (simulation d'ordres, P&L, balance)
- Détection de corrélations et signaux académiques (RSI, volume spike, momentum)

## Pages
- `/` : Screener pumps classique
- `/bot` : Robot testeur de stratégies (le plus puissant)

## Comment utiliser
1. Va sur `/bot`
2. Tape une paire USDC (ex: PEPEUSDC, BONKUSDC, ou n'importe quel token récent)
3. Clique "Analyser"
4. Le bot te donne sa recommandation avec explication
5. Clique LONG ou SHORT pour simuler le trade en démo
6. Observe le P&L et la balance évoluer

Parfait pour tester tes idées de trading sans risque et voir les erreurs/corrélations !

## Stack
Flask + ccxt + pandas + Plotly.js + Tailwind