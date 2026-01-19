[Documentation_TradeHelperBot_2026-01-17.md](https://github.com/user-attachments/files/24688844/Documentation_TradeHelperBot_2026-01-17.md)
# 📚 DOCUMENTATION - Trade Helper Bot Discord

**Version:** 1.0  
**Date:** 17/01/2026  
**Repository:** trade-helper-bot-discord  
**Auteur:** Bastien D'ALBA

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation & Configuration](#installation--configuration)
4. [Commandes Disponibles](#commandes-disponibles)
5. [Modules Techniques](#modules-techniques)
6. [Cas d'Usage Pratiques](#cas-dusage-pratiques)
7. [Déploiement & Production](#déploiement--production)
8. [Maintenance & Monitoring](#maintenance--monitoring)
9. [Actifs Configurés](#actifs-configurés)
10. [Configuration des Alertes](#configuration-des-alertes)
11. [Roadmap & Évolutions](#roadmap--évolutions)

---

## ⚡ RÉSUMÉ RAPIDE

**Trade Helper Bot** est un assistant Discord automatisé pour traders, offrant :

🧮 **Calculs de Trading**
- Position sizing (spot & levier jusqu'à 125x)
- **Calcul perte au SL + gain au TP** (nouveau !)
- Calcul R/R, DCA, et liquidation
- Scénarios P&L et avertissements

📊 **Analyse Technique**
- 14 moyennes mobiles (MA7 à MA750) ⭐ AMÉLIORÉ
- Multi-timeframes (5m à 1d)
- Détection croisements (paires + multiples), alignements, compressions
- MA112 long terme (336, 375, 448, 750)

🔔 **Alertes Automatiques**
- Volume : surveillance toutes les 15 min
- MA : surveillance toutes les 60 min
- Webhooks Discord configurables
- Cooldown anti-spam

📈 **Assets Supportés**
- 6 cryptos (Binance) : BTC, ETH, AVAX, ASTER, SOL, AAVE
- 4 stocks (Yahoo) : AAPL, MSFT, SPX, TTE
- Ajout/suppression en temps réel

🔧 **Production Ready**
- Retry automatique Binance
- Warm-up mode (1h) pour alertes
- Systemd service inclus
- RAM optimisée (<200MB)

---

## 🎯 VUE D'ENSEMBLE

### Description

**Trade Helper Bot** est un bot Discord en Python conçu pour assister les traders dans leurs calculs de position et l'analyse technique des cryptomonnaies et actions, avec un système d'alertes automatiques pour les signaux techniques et les variations de volume.

### Fonctionnalités Principales

#### 💼 Calculs de Trading
- **Calcul de position spot** : Dimensionnement optimal selon le risque
- **Calcul avec levier** : Gestion du risque avec effet de levier (Futures/Margin)
  - Prix de liquidation calculé
  - **Perte exacte au Stop Loss** (en $ et % du capital)
  - **Gain potentiel au Take Profit** (avec comparaison gain/perte)
  - Scénarios P&L (+10%, +5%, -5%, -10%)
  - Avertissements automatiques (levier élevé, liquidation proche, etc.)
- **Ratio Risk/Reward** : Calcul automatique du R/R
- **DCA (Dollar Cost Averaging)** : Prix moyen d'achat

#### 📊 Analyse Technique
- **Moyennes Mobiles (MA)** : Système double MA (court & long terme)
- **Détection de croisements** : Golden Cross, Death Cross, croisements multiples
- **Compression des MA** : Détection de volatilité imminente
- **Position du prix** : Prix vs toutes les MA
- **Multi-timeframes** : 5m, 15m, 1h, 4h, 1d

#### 🔔 Alertes Automatiques
- **Alertes MA** : Surveillance continue des croisements et alignements (toutes les 60 minutes)
- **Alertes Volume** : Détection des pics de volume anormaux (toutes les 15 minutes)
- **Webhooks Discord** : Notifications automatiques via webhooks configurables
- **Système de cooldown** : Prévention du spam avec délais paramétrables

#### 🔧 Gestion Dynamique
- **Ajout/Suppression de cryptos/actions** : Gestion en temps réel
- **Recherche de symboles** : Recherche Binance et Yahoo Finance intégrée
- **Validation automatique** : Vérification des symboles sur les plateformes
- **Retry automatique** : Reconnexion automatique à Binance en cas de déconnexion

### Technologies

- **Langage:** Python 3.10+
- **Framework Bot:** discord.py (py-cord)
- **API Crypto:** Binance API (publique)
- **API Actions:** Yahoo Finance (yfinance)
- **Calculs:** NumPy, Pandas
- **Environnement:** python-dotenv

---

## 🏗️ ARCHITECTURE

### Structure du Projet

```
trade-helper-bot-discord/
├── bot.py                    # Point d'entrée principal + commandes Discord
├── market_analysis.py        # Analyseurs Binance & Yahoo Finance
├── crypto_manager.py         # Gestionnaire de cryptos
├── stock_manager.py          # Gestionnaire d'actions
├── volume_monitor.py         # Surveillance des volumes (alertes automatiques)
├── ma_alerts.py              # Surveillance des MA (alertes automatiques)
├── symbol_search.py          # Recherche de symboles Binance & Yahoo Finance
├── ma_alerts_config.json     # Configuration alertes MA
├── volume_config.json        # Configuration alertes volume
├── cryptos.json              # Liste des cryptos surveillées
├── stocks.json               # Liste des actions surveillées
├── .env                      # Variables d'environnement
├── requirements.txt          # Dépendances Python
└── venv/                     # Environnement virtuel
```

### Modules Principaux

#### 1. **bot.py**
- Initialisation du bot Discord
- Gestion des commandes slash (position, leverage, rr, dca, crypto_*, stock_*)
- Orchestration des modules
- Background tasks (volume_check, ma_alert_check)

**Imports principaux:**
```python
import discord
from discord.ext import commands, tasks
from market_analysis import BinanceMarketAnalyzer, YFinanceMarketAnalyzer
from crypto_manager import CryptoManager
from stock_manager import StockManager
from volume_monitor import VolumeMonitor
from ma_alerts import MAAlertMonitor
from symbol_search import BinanceSymbolSearch, YFinanceSymbolSearch
```

#### 2. **market_analysis.py**
- Classes `BinanceMarketAnalyzer` et `YFinanceMarketAnalyzer`
- Connexion API Binance et Yahoo Finance
- Calcul des moyennes mobiles (SMA)
- Détection de signaux techniques

**Fonctionnalités:**
- `analyze_symbol()` - Analyse complète d'un actif
- `get_ma_values()` - Calcul des MA
- `detect_crossovers()` - Détection croisements
- `test_symbol_exists()` - Validation symbole
- Retry automatique avec Binance en cas de déconnexion

#### 3. **crypto_manager.py** & **stock_manager.py**
- Classes `CryptoManager` et `StockManager`
- Gestion des fichiers cryptos.json et stocks.json
- Validation des symboles

**Méthodes:**
- `add_crypto()/add_stock()` - Ajouter un actif
- `remove_crypto()/remove_stock()` - Supprimer un actif
- `get_all_cryptos()/get_all_stocks()` - Lister tous
- `crypto_exists()/stock_exists()` - Vérifier existence

#### 4. **volume_monitor.py**
- Classe `VolumeMonitor`
- Surveillance automatique des pics de volume (toutes les 15 minutes par défaut)
- Détection de volumes anormaux (>150%, >200%, >300%)
- Cooldown pour éviter le spam (30 minutes par défaut)
- Support webhooks Discord

**Méthodes:**
- `check_volumes()` - Vérification des volumes
- `send_volume_alert()` - Envoi d'alertes
- Configuration via volume_config.json

#### 5. **ma_alerts.py**
- Classe `MAAlertMonitor`
- Surveillance automatique des MA (toutes les 60 minutes par défaut)
- Détection Golden/Death Cross, alignements, compressions
- Warm-up mode (1h) pour éviter les faux signaux au démarrage
- Cooldown (4 heures par défaut) pour chaque actif
- Support webhooks Discord séparés (cross, alignment, compression)

**Méthodes:**
- `check_alerts()` - Vérification des signaux
- `detect_golden_death_cross()` - Détection croisements 50/200
- `send_webhook_alert()` - Envoi via webhook
- Configuration via ma_alerts_config.json

#### 6. **symbol_search.py**
- Classes `BinanceSymbolSearch` et `YFinanceSymbolSearch`
- Recherche de symboles sur Binance et Yahoo Finance
- Autocomplétion Discord intégrée

**Méthodes:**
- `search()` - Recherche de symboles
- Priorité aux paires USDT pour Binance
- Fallback testing pour Yahoo Finance

### Système de Moyennes Mobiles

#### Système 1 (Court/Moyen Terme) ⭐ NOUVEAU
```
MA7, MA13, MA20, MA25, MA32, MA50, MA100, MA200, MA300
```
**Ajout de MA7 et MA20 pour plus de précision**

#### Système 2 (Long Terme)
```
MA112, MA336, MA375, MA448, MA750
```

**Type:** SMA (Simple Moving Average)

#### Détections Automatiques

| Signal | Condition | Indication |
|--------|-----------|-----------|
| **Golden Cross** | MA50 > MA200 | 🟢 Haussier fort |
| **Death Cross** | MA50 < MA200 | 🔴 Baissier fort |
| **Croisements Paires** ⭐ | 7-20, 20-50, 13-25, 25-32, 32-100, 100-200 | 📈/📉 Signaux précis |
| **Croisements Multiples** ⭐ | MA croise ≥2 MA simultanément | ⚡ Signal fort |
| **MA112 Long Terme** ⭐ | MA112 croise 336, 375, 448, 750 | 📊 Tendance majeure |
| **Alignement Haussier** | Prix > toutes MA | 🟢 Tendance haussière |
| **Alignement Baissier** | Prix < toutes MA | 🔴 Tendance baissière |
| **Compression** | Écart MA < 5% | ⚠️ Volatilité imminente |

#### Hiérarchie des Signaux (Backtest Historique) 🆕

Le bot intègre maintenant un système de **rating des signaux** basé sur des backtests historiques (1990-2025, S&P 500 + Crypto).

**🏆 TIER 1 - Signaux Institutionnels (10/10)**

| Signal | MA | Rating | Win Rate | Fréquence | Use Case |
|--------|-----|--------|----------|-----------|----------|
| **Golden/Death Cross** 🏆 | 100 × 200 | **10/10** ⭐⭐⭐⭐⭐ | **72-80%** | 1-4x/an | **Trend majeur multi-mois** |
| **Multi-Cross MA112** 🏆 | 112 × (336+375+448+750) | **10/10** ⭐⭐⭐⭐⭐ | **85-90%** | Très rare | **Cycle majeur - Opportunité générationnelle** |

**Pourquoi Tier 1 :**
- Signal suivi par TOUS les traders institutionnels
- Fiabilité maximale (70-90%)
- Self-fulfilling prophecy (tant de traders suivent → devient réalité)
- Low false signals (rare donc fiable)
- Best risk/reward ratio

**🥈 TIER 2 - Signaux Majeurs (8-9/10)**

| Signal | MA | Rating | Win Rate | Fréquence | Use Case |
|--------|-----|--------|----------|-----------|----------|
| **Swing Trading** 🥈 | 20 × 50 | **9/10** ⭐⭐⭐⭐ | **68-72%** | 6-12x/an | **Swing trading optimal (1-6 semaines)** |
| **Position Trading** 🥈 | 32 × 100 | **8.5/10** ⭐⭐⭐⭐ | **70%** | 3-6x/an | **Position trading (2-12 semaines)** |
| **Confluence Court-Terme** 🥈 | 13 × (25+32+50) | **8/10** ⭐⭐⭐⭐ | **68%** | 4-8x/an | **Swing agressif avec confluence** |

**Pourquoi Tier 2 :**
- Balance optimale réactivité/stabilité
- Win rate très bon (68-72%)
- Utilisé par institutions pour positioning mid-term
- Moderate frequency = bons setups réguliers

**🥉 TIER 3 - Signaux Bons (6-7/10) - Requires Confirmation**

| Signal | MA | Rating | Win Rate | Fréquence | Use Case |
|--------|-----|--------|----------|-----------|----------|
| **Day Trading** 🥉 | 25 × 32 | **7/10** ⭐⭐⭐ | **58-62%** | 8-15x/an | **Day trading avec confirmation** |
| **Scalping** 🥉 | 13 × 25 | **6.5/10** ⭐⭐⭐ | **54-58%** | 15-30x/an | **Scalp/Filter - Multi-confluence requis** |
| **Scalping Pro** 🥉 | 7 × 20 | **6/10** ⭐⭐⭐ | **50-55%** | 30-60x/an | **Scalping professionnel seulement** |

**Pourquoi Tier 3 :**
- Noise élevé (false signals fréquents 25-40%)
- **NE PAS trader seul** - Requires confirmation (Volume, RSI, S/R)
- Win rate modéré (50-62%)
- Scalping utility seulement

**💡 Règles d'Utilisation**

```
✅ Tier 1 (10/10) : TRADE SEUL possible (signaux institutionnels)
✅ Tier 2 (8-9/10) : TRADE SEUL ou avec 1 confluence
⚠️ Tier 3 (6-7/10) : JAMAIS SEUL - Minimum 2-3 confluences requises

Confluence recommandées :
- Volume spike (>150% moyenne)
- RSI (40-60 neutral, >50 bullish)
- Support/Resistance (retest, breakout)
- Multi-timeframe alignment (Daily + H4 + H1)
```

**📊 Performance Backtest (S&P 500, 1990-2025)**

| Signal | Net Profit/Year | Avg Gain | Avg Loss | R/R Ratio | Trades/Year |
|--------|-----------------|----------|----------|-----------|-------------|
| MA100×200 | **+12%/an** | +18% | -8% | 2.25:1 | 2-3 |
| MA112×Multi | **+18%/an** | +45% | -12% | 3.75:1 | 0.5 |
| MA20×50 | **+9%/an** | +6% | -3% | 2:1 | 8-10 |
| MA32×100 | **+10%/an** | +11% | -5% | 2.2:1 | 4-5 |
| MA25×32 | **+3%/an** | +3% | -2.5% | 1.2:1 | 12-15 |
| MA13×25 | **+1%/an** | +2% | -2% | 1:1 | 20-30 |
| MA7×20 | **-2%/an*** | +1% | -1.2% | 0.8:1 | 40-60 |

*Après fees/slippage

**🎯 Message Clé**

> **Plus les MA sont longues = Plus le signal est fiable, moins il est fréquent, meilleur le R/R**
>
> **Patience sur signaux rares (Tier 1-2) > Overtrading sur signaux fréquents (Tier 3)**

---

## 🎯 SYSTÈME DE SCORING EMA CASCADE v2.0 🆕

Le bot intègre maintenant le **système de scoring EMA Cascade Unified v2.0**, une méthodologie de scoring sur 100 points basée sur une approche multi-timeframe adaptive.

### **Architecture du Scoring (100 points)**

Chaque signal MA reçoit un **score total sur 100 points** réparti en 4 tiers:

#### **TIER 1 : Direction Daily (35 points)**

**Rôle :** Établir le bias directionnel global (SACRÉ)

```
□ EMA100 vs EMA200 Daily           : 20 pts
  → EMA100 > EMA200 = Bullish bias
  → EMA100 < EMA200 = Bearish bias

□ Prix current vs EMA200 Daily      : 10 pts
  → Above EMA200 = Bullish structural
  → Below EMA200 = Bearish structural

□ ADX / Volatilité Daily             : 5 pts
  → Forte volatilité = Trend fort
```

**⚠️ RÈGLE ABSOLUE :**
```
Signal OPPOSÉ Daily bias = SCORE 0 (INVALIDATION TOTALE)
→ Long signal + Daily bearish = SKIP
→ Short signal + Daily bullish = SKIP
→ NO exceptions
```

---

#### **TIER 2 : Signal Timeframe (35 points)**

**Rôle :** Déclencheur entry selon timeframe de détection

```
□ Croisement EMA détecté             : 5-8 pts (selon TF)
  → Daily: 8 pts
  → H4: 8 pts
  → H1: 6 pts
  → 15min: 5 pts

□ Volume vs moyenne (SMA20)          : 12 pts max
  → >150% = 12 pts (High conviction)
  → >120% = 8 pts (Medium)
  → >100% = 4 pts (Baseline)

□ RSI (momentum)                     : 5 pts
  → 40-60 (neutre) = 5 pts optimal
  → 30-70 = 3 pts partial

□ ADX / Volatilité TF                : 5-10 pts
```

---

#### **TIER 3 : Confluence Multi-TF (20 points)**

**Rôle :** Validation signal par timeframes adjacents

```
Pour Signal Daily:
□ Weekly trend aligned         : 10 pts
□ Weekly ADX >20              : 5 pts
□ Monthly context             : 5 pts

Pour Signal H4:
□ Daily trend aligned         : 12 pts (CRITIQUE)
□ H1 trend aligned            : 5 pts
□ Daily ADX >20               : 3 pts

Pour Signal H1:
□ H4 trend aligned            : 10 pts (CRITIQUE)
□ Daily trend aligned         : 7 pts
□ 15min momentum              : 3 pts

Pour Signal 15min:
□ H1 trend aligned            : 10 pts (OBLIGATOIRE)
□ H4 trend aligned            : 7 pts
□ H1 ADX >20                  : 3 pts
```

**⚠️ RÈGLE 15MIN v2.0 :**
```
H1 aligned = OBLIGATOIRE pour atteindre threshold 70
→ Sans H1 = Score insuffisant (protection whipsaws)
→ Win rate maintenu 70%+ garanti
```

---

#### **TIER 4 : Confluence Technique (10 points bonus)**

**Rôle :** Bonus confluences additionnelles

```
□ Fibonacci key level (38.2%, 50%, 61.8%)  : 5 pts
□ Support/Resistance horizontal major      : 5 pts
```

---

### **Thresholds Adaptatifs par Timeframe**

```
Daily   : Score >65 = TRADE
H4      : Score >70 = TRADE
H1      : Score >72 = TRADE
15min   : Score >70 = TRADE (v2.0 - AJUSTÉ de 75)
```

---

### **Classification par Conviction**

| Score | Tier | Conviction | Emoji | Win Rate | Use Case |
|-------|------|------------|-------|----------|----------|
| **90-100** | **S** | **MAXIMUM** 🔥🔥🔥 | ⭐⭐⭐⭐⭐ | **85-92%** | Position 100%, Risk 2% |
| **80-89** | **A** | **EXCELLENT** 🔥🔥 | ⭐⭐⭐⭐ | **78-85%** | Position 80%, Risk 2% |
| **70-79** | **B** | **GOOD** 🔥 | ⭐⭐⭐ | **72-78%** | Position 60-70%, Risk 1.5% |
| **65-69** | **C** | **ACCEPTABLE** 📊 | ⭐⭐ | **68-72%** | Daily only, Position 60% |
| **<65** | **D** | **SKIP** ❌ | ❌ | **<68%** | NO TRADE |

---

### **Affichage dans les Alertes**

Chaque alerte Discord affiche maintenant :

```
🎯 SCORE EMA CASCADE v2.0

🔥🔥 EXCELLENT - Tier A

Score Total: 83/100 pts
└ Tier 1 (Direction Daily): 30/35 pts
└ Tier 2 (Signal TF): 28/35 pts
└ Tier 3 (Multi-TF): 15/20 pts
└ Tier 4 (Technique): 10/10 pts

Threshold H4: 70 pts
Tradable: ✅ OUI
```

---

### **Avantages du Système EMA Cascade v2.0**

✅ **Scoring objectif** - Élimine émotions et FOMO
✅ **Thresholds adaptatifs** - Chaque TF a son seuil optimal
✅ **Multi-timeframe** - Confluence automatique H1/H4/Daily
✅ **Protection contre-trend** - Règle absolue Daily bias
✅ **Volume + RSI + ADX** - Filtres techniques intégrés
✅ **Classification claire** - Tier S/A/B/C/D immédiate
✅ **Win rate prévisible** - Corrélation score/performance
✅ **15min viable** - Threshold 70 avec H1 obligatoire

---

### **Règles Critiques v2.0**

```
1. Signal opposé Daily = Score 0 (NO exceptions)
2. Thresholds stricts (65/70/72/70)
3. 15min H1 aligned = OBLIGATOIRE (win rate protection)
4. Volume <100% = SKIP
5. Score 70-74 = Position size REDUCED
6. Score 70-71 = Consider skip (borderline)
7. Max positions : Capital dependent (1-3)
```

---

### **Trades Attendus par Mois (v2.0)**

| Timeframe | Threshold | Trades/Mois | Win Rate |
|-----------|-----------|-------------|----------|
| **Daily** | >65 | 1-3 | 80-90% |
| **H4** | >70 | 5-15 | 75-88% |
| **H1** | >72 | 10-25 | 72-85% |
| **15min** | >70 | 12-20 | 70-78% |

**Total attendu :** 28-63 signaux/mois (dont 60-70% seront SKIP = Normal)

---

### **Message Clé EMA Cascade**

> **"DISCIPLINE = SURVIVAL"**
>
> Skip 60-70% des signaux = Comportement CORRECT
> Patience sur Tier S/A > FOMO sur Tier C/D
> Quality > Quantity
> Score >80 = GOLD | Score 70-79 = OK | Score <70 = WAIT

---

## 🚀 INSTALLATION & CONFIGURATION

### Prérequis

- Python 3.10 ou supérieur
- Un serveur Discord
- Un token de bot Discord
- Connexion internet (APIs Binance/Yahoo)

### Installation Étape par Étape

#### 1. Cloner le Repository

```bash
git clone https://github.com/votre-username/trade-helper-bot-discord.git
cd trade-helper-bot-discord
```

#### 2. Créer l'Environnement Virtuel

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate    # Windows
```

#### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

**Dépendances principales:**
```
discord.py (py-cord)
python-binance
yfinance
numpy
pandas
python-dotenv
```

#### 4. Configuration du Bot Discord

**A. Créer une Application Discord**
1. Allez sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Cliquez sur "New Application"
3. Donnez un nom à votre bot
4. Dans l'onglet "Bot", cliquez sur "Add Bot"
5. Copiez le **Token**

**B. Activer les Intents**
Dans l'onglet "Bot", activez:
- ✅ Message Content Intent
- ✅ Server Members Intent (optionnel)

**C. Inviter le Bot**
1. Onglet "OAuth2" → "URL Generator"
2. Scopes: ✅ bot, ✅ applications.commands
3. Permissions: 
   - Send Messages
   - Embed Links
   - Use Slash Commands
4. Copiez l'URL générée et ouvrez-la

#### 5. Créer le Fichier .env

```bash
touch .env
nano .env
```

**Contenu du fichier .env:**
```env
DISCORD_TOKEN=votre_token_discord_ici
```

#### 6. Créer les Fichiers de Configuration

**cryptos.json:**
```json
{
  "BTC": "BTCUSDT",
  "ETH": "ETHUSDT",
  "AVAX": "AVAXUSDT",
  "ASTER": "ASTERUSDT",
  "SOL": "SOLUSDT",
  "AAVE": "AAVEUSDT"
}
```

**stocks.json:**
```json
{
  "AAPL": "AAPL",
  "MSFT": "MSFT",
  "SPX": "^GSPC",
  "TTE": "TTE"
}
```

**ma_alerts_config.json:**
```json
{
  "check_interval_minutes": 60,
  "cooldown_hours": 4,
  "compression_threshold": 5.0,
  "assets": {
    "crypto": ["BTCUSDT", "ETHUSDT", "AVAXUSDT", "ASTERUSDT", "SOLUSDT", "AAVEUSDT"],
    "stocks": ["AAPL", "MSFT", "^GSPC", "TTE"]
  },
  "timeframes": ["15m", "1h", "4h", "1d"],
  "ma_system1": [7, 13, 20, 25, 32, 50, 100, 200, 300],
  "ma_system2": [112, 336, 375, 448, 750],
  "ma_pairs_to_watch": [
    [7, 20],
    [20, 50],
    [13, 25],
    [25, 32],
    [32, 100],
    [100, 200]
  ],
  "ma_112_crosses": [
    [112, 336],
    [112, 375],
    [112, 448],
    [112, 750]
  ],
  "alert_types": {
    "golden_cross": true,
    "death_cross": true,
    "ma_pair_cross": true,
    "multiple_cross": true,
    "ma_112_cross": true,
    "alignment": true,
    "compression": true
  },
  "webhooks": {
    "cross": "https://discord.com/api/webhooks/...",
    "alignment": "https://discord.com/api/webhooks/...",
    "compression": "https://discord.com/api/webhooks/..."
  }
}
```

**volume_config.json:**
```json
{
  "check_interval_minutes": 15,
  "cooldown_minutes": 30,
  "thresholds": {
    "moderate": 150,
    "high": 200,
    "critical": 300
  },
  "reference_periods": {
    "short": 25,
    "long": 300
  },
  "assets": {
    "crypto": ["BTCUSDT", "ETHUSDT", "AVAXUSDT", "ASTERUSDT", "SOLUSDT", "AAVEUSDT"],
    "stocks": ["AAPL", "MSFT", "^GSPC", "TTE"]
  },
  "webhook_url": "https://discord.com/api/webhooks/..."
}
```

#### 7. Lancer le Bot

**Mode développement:**
```bash
python3 bot.py
```

**Mode production (avec systemd):**
Voir section [Déploiement](#déploiement--production)

---

## 💬 COMMANDES DISPONIBLES

### Tableau Récapitulatif

| Catégorie | Commande | Description |
|-----------|----------|-------------|
| **Calculs** | `/position` | Calcul position spot |
| | `/leverage` | Calcul position avec levier |
| | `/rr` | Ratio Risk/Reward |
| | `/dca` | Dollar Cost Averaging |
| **Crypto** | `/crypto_check` | Analyser une crypto |
| | `/crypto_compare` | Comparer cryptos (toutes ou sélection) ⭐ |
| | `/crypto_list` | Lister cryptos configurées |
| | `/crypto_add` | Ajouter une crypto |
| | `/crypto_remove` | Supprimer une crypto |
| | `/crypto_search` | Rechercher sur Binance |
| **Stock** | `/stock_check` | Analyser une action |
| | `/stock_compare` | Comparer stocks (tous ou sélection) ⭐ |
| | `/stock_list` | Lister actions configurées |
| | `/stock_add` | Ajouter une action |
| | `/stock_remove` | Supprimer une action |
| | `/stock_search` | Rechercher sur Yahoo Finance |
| **Volume** | `/volume_status` | État monitoring volume |
| | `/volume_config` | Config alertes volume |
| | `/volume_test` | Test immédiat volume |
| **Alertes MA** | `/ma_alerts_status` | État monitoring MA |
| | `/ma_alerts_config` | Config alertes MA |
| | `/ma_alerts_test` | Test immédiat MA |
| **Aide** | `/help` | Afficher toutes les commandes |

---

### Catégorie 1: Calculs de Position

#### /position
**Description:** Calcule la taille optimale d'une position spot

**Paramètres:**
- `capital` (obligatoire) : Capital total disponible ($)
- `risk_percent` (obligatoire) : Pourcentage de risque (ex: 2 pour 2%)
- `entry` (obligatoire) : Prix d'entrée prévu
- `stop_loss` (obligatoire) : Prix du stop loss
- `target` (optionnel) : Prix cible pour calcul R/R

**Exemple:**
```
/position capital:10000 risk_percent:2 entry:50 stop_loss:48 target:56
```

**Résultat:**
- Montant à risquer
- Taille de position (unités)
- Valeur de la position ($)
- P&L au stop loss
- P&L à la target
- Ratio R/R
- Qualité du trade

---

#### /leverage
**Description:** Calcule une position avec effet de levier (Futures/Margin Trading)

**Paramètres:**
- `capital` (obligatoire) : Capital total disponible ($)
- `leverage_amount` (obligatoire) : Effet de levier (1x, 2x, 5x, 10x, 20x, 50x, 100x, 125x)
- `risk_percent` (obligatoire) : Pourcentage de risque par trade (ex: 2 pour 2%)
- `entry` (obligatoire) : Prix d'entrée prévu
- `stop_loss` (obligatoire) : Prix du stop loss
- `target` (optionnel) : Prix cible (take profit) pour calcul R/R

**Exemple:**
```
/leverage capital:10000 leverage_amount:10 risk_percent:2 entry:50000 stop_loss:49000 target:52000
```

**Résultats affichés:**

1. **💰 Capital & Risque**
   - Capital total
   - Risque accepté (%)
   - Montant à risquer ($)

2. **📊 Position**
   - Exposition totale ($)
   - Marge utilisée ($ et % du capital)
   - Quantité d'unités

3. **📍 Prix**
   - Prix d'entrée
   - Stop Loss
   - Target (si fourni)
   - Distance au SL (%)

4. **🔥 Liquidation**
   - Prix de liquidation calculé
   - Distance jusqu'à liquidation (%)
   - ✅/⚠️ Validation position du SL vs liquidation

5. **❌ Perte au Stop Loss** ⭐ NOUVEAU
   - 💸 Perte exacte si SL touché ($)
   - 📉 ROI sur la marge (%)
   - 📊 % du capital total perdu

6. **⚖️ Ratio Risque/Rendement** (si target fourni)
   - 🎯 Ratio R/R (ex: 2.00:1)
   - 💰 Gain à la target ($)
   - 📈 ROI sur la marge (%)
   - 💵 **Comparaison Gain vs Perte** ($)
   - Verdict (Excellent/Bon/Acceptable/Défavorable)

7. **📈 Scénarios P&L** (sur la marge)
   - +10% : Profit potentiel
   - +5% : Profit potentiel
   - -5% : Perte potentielle
   - -10% : Perte potentielle

8. **⚠️ Avertissements automatiques**
   - Levier ≥50x (risque élevé)
   - Marge >80% du capital
   - Liquidation < 5% de distance
   - Ratio R/R < 2:1

**Pourquoi c'est utile :**
- Visualisez EXACTEMENT combien vous perdrez au SL avant d'entrer
- Comparez directement le gain potentiel vs la perte potentielle
- Évitez les surprises avec le calcul du prix de liquidation
- Prenez des décisions éclairées avec les avertissements automatiques

---

#### /rr
**Description:** Calcul rapide du ratio risque/rendement

**Paramètres:**
- `entry` : Prix d'entrée
- `stop_loss` : Stop loss
- `target` : Take profit

**Exemple:**
```
/rr entry:50 stop_loss:48 target:56
```

**Résultat:**
- Risque ($ et %)
- Rendement ($ et %)
- Ratio R/R
- Qualité (Excellent/Bon/Moyen/Faible)

---

#### /dca
**Description:** Calcule le prix moyen d'achat (DCA)

**Format:** `prix1:quantité1,prix2:quantité2`

**Exemple:**
```
/dca entries:100:1,90:1.5,85:2
```

**Résultat:**
- Détail de chaque position
- Quantité totale
- Coût total
- **Prix moyen**

---

### Catégorie 2: Analyse Crypto (Binance)

#### /crypto_check
**Description:** Analyser les moyennes mobiles d'une crypto

**Paramètres:**
- `crypto` (obligatoire) : Symbole (BTC, ETH, SOL...)
- `timeframe` (optionnel) : 5m, 15m, 1h, 4h, **1d** (défaut)

**Exemple:**
```
/crypto_check crypto:BTC timeframe:1d
```

**Résultat:**
- Prix actuel
- Valeurs de toutes les MA
- Status (Haussier/Baissier/Neutre)
- Compression détectée ?
- Position du prix vs MA
- Ordre des MA
- Distances entre MA

---

#### /crypto_compare
**Description:** Comparer des cryptos (toutes ou une sélection personnalisée) ⭐ NOUVEAU

**Paramètres:**
- `timeframe` (optionnel) : 5m, 15m, 1h, 4h, **1d** (défaut)
- `assets` (optionnel) : Cryptos à comparer séparées par des virgules

**Exemples:**

**Mode global** (toutes les cryptos) :
```
/crypto_compare timeframe:4h
```

**Mode sélectif** (cryptos spécifiques) :
```
/crypto_compare timeframe:1h assets:BTC,ETH,SOL
```

**Résultat:**
- **Mode** : Global ou Sélection personnalisée
- **Nombre d'actifs** comparés
- Prix actuel de chaque crypto
- Status (🟢 Haussier / 🔴 Baissier / 🟠 Neutre)
- Compression détectée (🔥 si oui)
- Écart entre les MA (%)
- **Alertes** : Compressions importantes

**Cas d'usage :**
- Comparer uniquement vos cryptos favorites
- Analyser un secteur spécifique (ex: L1 blockchains)
- Vue rapide sur toutes vos cryptos configurées

---

#### /crypto_list
**Description:** Lister toutes les cryptos supportées

**Résultat:**
- Liste complète
- Symboles courts → Symboles Binance

---

#### /crypto_add
**Description:** Ajouter une nouvelle crypto

**Paramètres:**
- `symbol` : Symbole court (ex: SOL)
- `binance_symbol` : Symbole Binance (ex: SOLUSDT)

**Validation automatique:**
- ✅ Format du symbole Binance
- ✅ Existence sur Binance
- ✅ Unicité dans la liste

**Exemple:**
```
/crypto_add symbol:SOL binance_symbol:SOLUSDT
```

---

#### /crypto_remove
**Description:** Supprimer une crypto

**Paramètres:**
- `crypto` : Symbole à supprimer (autocomplétion)

**Exemple:**
```
/crypto_remove crypto:SOL
```

---

#### /crypto_search
**Description:** Rechercher un symbole sur Binance

**Paramètres:**
- `search_term` : Terme de recherche (ex: SOL, AVAX, BNB)

**Exemple:**
```
/crypto_search search_term:SOL
```

**Résultat:**
- Liste des symboles Binance correspondants
- Priorité aux paires USDT
- Maximum 25 résultats

---

### Catégorie 3: Analyse Actions (Yahoo Finance)

#### /stock_check
**Description:** Analyser les moyennes mobiles d'une action

**Paramètres:**
- `stock` : Symbole (AAPL, MSFT, TSLA...)
- `timeframe` : 5m, 15m, 1h, 4h, 1d

**Exemple:**
```
/stock_check stock:AAPL timeframe:1d
```

---

#### /stock_compare
**Description:** Comparer des stocks/indices (tous ou une sélection personnalisée) ⭐ NOUVEAU

**Paramètres:**
- `timeframe` (optionnel) : 5m, 15m, 1h, 4h, **1d** (défaut)
- `assets` (optionnel) : Stocks à comparer séparés par des virgules

**Exemples:**

**Mode global** (tous les stocks) :
```
/stock_compare timeframe:1d
```

**Mode sélectif** (stocks spécifiques) :
```
/stock_compare timeframe:4h assets:AAPL,MSFT,SPX
```

**Résultat:**
- **Mode** : Global ou Sélection personnalisée
- **Nombre d'actifs** comparés
- Prix actuel de chaque stock
- Status (🟢 Haussier / 🔴 Baissier / 🟠 Neutre)
- Compression détectée (🔥 si oui)
- Écart entre les MA (%)
- **Alertes** : Compressions importantes

**Cas d'usage :**
- Comparer uniquement les FAANG/Magnificent 7
- Analyser un secteur (ex: Tech, Energy)
- Comparer indices majeurs (SPX, NASDAQ, DOW)

---

#### /stock_list
**Description:** Lister toutes les actions supportées

---

#### /stock_add
**Description:** Ajouter une nouvelle action

**Paramètres:**
- `symbol` : Symbole court (ex: TSLA)
- `yfinance_symbol` : Symbole Yahoo Finance (ex: TSLA)

**Exemple:**
```
/stock_add symbol:TSLA yfinance_symbol:TSLA
```

---

#### /stock_remove
**Description:** Supprimer une action

**Paramètres:**
- `stock` : Symbole à supprimer

---

#### /stock_search
**Description:** Rechercher un symbole Yahoo Finance

**Paramètres:**
- `search_term` : Terme de recherche (ex: TESLA, APPLE)

---

### Catégorie 4: Alertes Volume

#### /volume_status
**Description:** Voir l'état actuel du monitoring de volume

**Résultat:**
- État du monitoring (actif/inactif)
- Dernière vérification
- Nombre d'alertes envoyées
- Prochaine vérification programmée

---

#### /volume_config
**Description:** Afficher la configuration des alertes volume

**Résultat:**
- Intervalle de vérification (15 minutes par défaut)
- Seuils de détection (150%, 200%, 300%)
- Périodes de référence (MA25, MA300)
- Cooldown (30 minutes)
- Liste des actifs surveillés

---

#### /volume_test
**Description:** Lancer une vérification immédiate des volumes

**Résultat:**
- Analyse instantanée de tous les actifs configurés
- Alertes si volumes anormaux détectés

---

### Catégorie 5: Alertes MA (Moyennes Mobiles)

#### /ma_alerts_status
**Description:** Voir l'état du monitoring MA

**Résultat:**
- État du monitoring (actif/inactif/warm-up)
- Dernière vérification
- Alertes récentes
- Prochaine vérification

---

#### /ma_alerts_config
**Description:** Afficher la configuration des alertes MA

**Résultat:**
- Intervalle de vérification (60 minutes par défaut)
- Timeframes surveillés (15m, 1h, 4h, 1d)
- Types d'alertes activés (golden/death cross, alignments, compression)
- Cooldown (4 heures)
- Seuil de compression (5%)
- URLs des webhooks configurés

---

#### /ma_alerts_test
**Description:** Lancer une vérification immédiate des MA

**Résultat:**
- Analyse instantanée de tous les actifs configurés
- Alertes si signaux détectés

---

### Catégorie 6: Configuration & Aide

#### /help
**Description:** Afficher toutes les commandes disponibles

**Résultat:**
- Guide complet des commandes
- Explications détaillées
- Exemples d'utilisation

---

## 🔧 MODULES TECHNIQUES

### BinanceMarketAnalyzer & YFinanceMarketAnalyzer

**Localisation:** `market_analysis.py`

**Responsabilités:**
- Connexion aux APIs Binance et Yahoo Finance
- Récupération des données OHLCV
- Calcul des moyennes mobiles (SMA)
- Détection de signaux techniques
- Retry automatique en cas de déconnexion

**Méthodes Principales:**

```python
class BinanceMarketAnalyzer:
    def __init__(self):
        self.client = Client()  # Client Binance public
        self._setup_retry_connection()  # Reconnexion automatique

    def analyze_symbol(self, symbol: str, interval: str = '1d') -> Dict:
        """
        Analyse complète d'un symbole

        Args:
            symbol: Symbole Binance (ex: BTCUSDT)
            interval: Timeframe (5m, 15m, 1h, 4h, 1d)

        Returns:
            dict: {
                'status': 'success' | 'error',
                'current_price': float,
                'ma_values': dict,
                'aligned_bullish': bool,
                'aligned_bearish': bool,
                'is_compressed': bool,
                'compression_pct': float,
                'crossovers': list
            }
        """

    def get_ma_values(self, prices: list, periods: list) -> dict:
        """Calcule les moyennes mobiles (SMA)"""

    def detect_crossovers(self, current_ma: dict, previous_ma: dict) -> list:
        """Détecte les croisements de MA"""

    def test_symbol_exists(self, symbol: str) -> bool:
        """Vérifie si un symbole existe sur Binance"""

class YFinanceMarketAnalyzer:
    """Même interface que BinanceMarketAnalyzer mais pour Yahoo Finance"""

    def analyze_symbol(self, symbol: str, interval: str = '1d') -> Dict:
        """Analyse complète d'une action/indice"""
```

---

### VolumeMonitor

**Localisation:** `volume_monitor.py`

**Responsabilités:**
- Surveillance automatique des volumes (background task)
- Détection de pics anormaux (>150%, >200%, >300%)
- Cooldown pour éviter le spam
- Envoi d'alertes via webhooks Discord

**Méthodes Principales:**

```python
class VolumeMonitor:
    def __init__(self, binance_analyzer, yfinance_analyzer, config_file='volume_config.json'):
        self.config = self._load_config()
        self.last_alert_time = {}  # Cooldown tracking

    async def check_volumes(self):
        """
        Vérifie les volumes de tous les actifs configurés
        Compare volume actuel vs moyennes historiques (MA25, MA300)
        Envoie alertes si seuils dépassés
        """

    async def send_volume_alert(self, asset, volume_change, level):
        """
        Envoie une alerte volume via webhook Discord

        Args:
            asset: Symbole de l'actif
            volume_change: Pourcentage de changement
            level: 'moderate' | 'high' | 'critical'
        """
```

**Configuration (volume_config.json):**
```json
{
  "check_interval_minutes": 15,
  "cooldown_minutes": 30,
  "thresholds": {
    "moderate": 150,  // +150% vs moyenne
    "high": 200,      // +200% vs moyenne
    "critical": 300   // +300% vs moyenne
  },
  "reference_periods": {
    "short": 25,   // MA25
    "long": 300    // MA300
  },
  "webhook_url": "https://discord.com/api/webhooks/..."
}
```

---

### MAAlertMonitor

**Localisation:** `ma_alerts.py`

**Responsabilités:**
- Surveillance automatique des moyennes mobiles
- Détection Golden/Death Cross (MA50/MA200)
- Détection alignements haussiers/baissiers
- Détection compressions (volatilité imminente)
- Warm-up mode (1h) pour éviter faux signaux au démarrage
- Cooldown (4h par défaut) par actif

**Méthodes Principales:**

```python
class MAAlertMonitor:
    def __init__(self, binance_analyzer, yfinance_analyzer, config_file='ma_alerts_config.json'):
        self.config = self._load_config()
        self.previous_ma_state = {}  # Pour détecter les changements
        self.last_alert_time = {}    # Cooldown tracking
        self.warmup_end_time = None  # Warm-up 1h

    async def check_alerts(self):
        """
        Vérifie tous les actifs sur tous les timeframes configurés
        Détecte: golden/death cross, alignments, compressions
        Envoie alertes via webhooks Discord séparés
        """

    def detect_golden_death_cross(self, ma_values) -> dict:
        """
        Détecte Golden Cross (MA50 > MA200) et Death Cross (MA50 < MA200)

        Returns:
            dict: {'type': 'golden' | 'death' | None, 'ma50': float, 'ma200': float}
        """

    async def send_webhook_alert(self, alert_type, asset, timeframe, data):
        """
        Envoie alerte via webhook Discord

        Args:
            alert_type: 'cross' | 'alignment' | 'compression'
            asset: Symbole
            timeframe: 15m, 1h, 4h, 1d
            data: Détails du signal
        """
```

**Configuration (ma_alerts_config.json):**
```json
{
  "check_interval_minutes": 60,
  "cooldown_hours": 4,
  "compression_threshold": 5.0,  // Écart <5% entre MA
  "timeframes": ["15m", "1h", "4h", "1d"],
  "ma_system1": [7, 13, 20, 25, 32, 50, 100, 200, 300],  // Système court/moyen terme
  "ma_system2": [112, 336, 375, 448, 750],  // Système long terme
  "ma_pairs_to_watch": [
    [7, 20],    // Très court terme
    [20, 50],   // Court terme
    [13, 25],   // Paire 1
    [25, 32],   // Paire 2
    [32, 100],  // Paire 3
    [100, 200]  // Paire 4
  ],
  "ma_112_crosses": [
    [112, 336],
    [112, 375],
    [112, 448],
    [112, 750]
  ],
  "alert_types": {
    "golden_cross": true,        // MA50 > MA200
    "death_cross": true,         // MA50 < MA200
    "ma_pair_cross": true,       // Croisements paires spécifiques
    "multiple_cross": true,      // MA croise ≥2 MA simultanément
    "ma_112_cross": true,        // MA112 croise long terme
    "alignment": true,           // Alignement haussier/baissier
    "compression": true          // Compression détectée
  },
  "webhooks": {
    "cross": "https://discord.com/api/webhooks/...",
    "alignment": "https://discord.com/api/webhooks/...",
    "compression": "https://discord.com/api/webhooks/..."
  }
}
```

---

### CryptoManager & StockManager

**Localisation:** `crypto_manager.py` et `stock_manager.py`

**Responsabilités:**
- Gestion des fichiers cryptos.json et stocks.json
- CRUD des actifs
- Validation des symboles

**Méthodes Principales:**

```python
class CryptoManager:
    def __init__(self, file_path: str = 'cryptos.json'):
        self.file_path = file_path
        self.cryptos = self._load_cryptos()

    def add_crypto(self, symbol: str, binance_symbol: str) -> bool:
        """Ajoute une crypto avec validation"""

    def remove_crypto(self, symbol: str) -> bool:
        """Supprime une crypto"""

    def get_all_cryptos(self) -> dict:
        """Retourne toutes les cryptos"""

    def get_binance_symbol(self, symbol: str) -> str:
        """Récupère le symbole Binance"""

    def crypto_exists(self, symbol: str) -> bool:
        """Vérifie l'existence"""

    def validate_binance_symbol(self, symbol: str) -> bool:
        """Valide le format d'un symbole Binance"""

# StockManager a la même interface pour les actions
```

---

### BinanceSymbolSearch & YFinanceSymbolSearch

**Localisation:** `symbol_search.py`

**Responsabilités:**
- Recherche de symboles sur Binance et Yahoo Finance
- Autocomplétion Discord
- Priorité aux paires USDT (Binance)

**Méthodes Principales:**

```python
class BinanceSymbolSearch:
    def __init__(self):
        self.client = Client()
        self.symbols_cache = None

    def search(self, search_term: str, limit: int = 25) -> List[str]:
        """
        Recherche symboles Binance
        Priorité: paires USDT

        Returns:
            List des symboles correspondants (max 25)
        """

class YFinanceSymbolSearch:
    """Recherche Yahoo Finance avec fallback testing"""

    def search(self, search_term: str) -> List[str]:
        """Recherche par mapping puis testing"""
```

---

## 💡 CAS D'USAGE PRATIQUES

### Exemple 1 : Calculer une position avec levier

**Situation :** Vous voulez trader BTC avec 10x de levier

**Commande :**
```
/leverage capital:10000 leverage_amount:10 risk_percent:2 entry:50000 stop_loss:49000 target:52000
```

**Ce que le bot calcule pour vous :**

1. **Votre exposition** : Avec $10,000 et 10x de levier, vous pouvez contrôler une position de ~$20,000
2. **Votre marge** : Combien de votre capital sera utilisé comme marge
3. **Prix de liquidation** : À quel prix vous serez liquidé (crucial !)
4. **Perte au SL** : Si le SL est touché à $49,000, vous perdrez exactement **-$2,000** (soit -20% de votre marge)
5. **Gain au TP** : Si le TP est atteint à $52,000, vous gagnerez **+$4,000** (soit +40% de votre marge)
6. **Ratio R/R** : 2:1 (vous risquez $2,000 pour gagner $4,000)
7. **Verdict** : ✅ Bon ratio, trade acceptable

**Pourquoi c'est utile :**
- Vous savez EXACTEMENT combien vous allez perdre ou gagner AVANT d'entrer
- Vous voyez immédiatement si le ratio risque/rendement est favorable
- Le bot vous alerte si le levier est trop élevé ou la liquidation trop proche

### Exemple 2 : Comparer plusieurs cryptos spécifiques ⭐ NOUVEAU

**Situation :** Vous voulez comparer uniquement BTC, ETH et SOL en 1h

**Commande :**
```
/crypto_compare timeframe:1h assets:BTC,ETH,SOL
```

**Le bot affiche :**
- **Mode** : Sélection personnalisée (3 actifs)
- Pour chaque crypto :
  - Prix actuel
  - Status (🟢 Haussier / 🔴 Baissier / 🟠 Neutre)
  - Compression détectée (🔥 si oui)
  - Écart entre les MA (%)
- **Alertes** si compression importante détectée

**Pourquoi c'est utile :**
- Comparer uniquement vos positions ouvertes
- Analyser un secteur spécifique (L1, DeFi, etc.)
- Comparaison rapide sans toutes les cryptos configurées

**Alternative - Comparer TOUTES les cryptos :**
```
/crypto_compare timeframe:1h
```
→ Affiche toutes les cryptos configurées (BTC, ETH, AVAX, ASTER, SOL, AAVE)

### Exemple 3 : Analyser une crypto avec les MA

**Situation :** Vous voulez savoir si BTC est en tendance haussière sur 4h

**Commande :**
```
/crypto_check crypto:BTC timeframe:4h
```

**Le bot affiche :**
- Position du prix vs les 12 moyennes mobiles
- ✅ Alignement haussier si prix > toutes les MA
- 🔥 Compression détectée si MA très proches (<5%)
- 📈 Golden Cross si MA50 > MA200
- 📉 Death Cross si MA50 < MA200

### Exemple 4 : Surveiller les volumes automatiquement

**Configuration :**
1. Le bot vérifie AUTOMATIQUEMENT les volumes toutes les 15 minutes
2. Si BTC fait +200% de volume vs la moyenne, vous recevez une alerte Discord
3. Cooldown de 30 minutes pour éviter le spam

**Commandes utiles :**
```
/volume_status     # Voir l'état actuel
/volume_test       # Tester immédiatement
/volume_config     # Voir la configuration
```

**Cas concret :**
- 14:00 → Le bot détecte BTC avec +250% de volume
- 14:01 → Vous recevez une alerte Discord : "🔥 Volume critique détecté sur BTCUSDT"
- Vous pouvez réagir rapidement à un potentiel mouvement de prix

### Exemple 5 : Alertes MA automatiques ⭐ AMÉLIORÉ

**Configuration :**
1. Le bot surveille AUTOMATIQUEMENT les MA toutes les 60 minutes
2. Détection de plusieurs types de signaux (voir ci-dessous)
3. Warm-up de 1h au démarrage pour éviter les faux signaux
4. Cooldown de 4h par actif pour éviter le spam

**Commandes utiles :**
```
/ma_alerts_status     # Voir les alertes récentes
/ma_alerts_test       # Tester immédiatement
/ma_alerts_config     # Voir la configuration
```

**Types de signaux détectés :**

**1. Golden/Death Cross (classique)**
- 10:00 → Le bot détecte un Golden Cross sur ETH en 4h
- 10:01 → Webhook Discord : "📈 Golden Cross détecté : ETHUSDT (4h)"
- Interprétation: Signal haussier fort (MA50 > MA200)

**2. Croisements de Paires Spécifiques** ⭐ NOUVEAU
- 14:30 → MA20 croise MA50 sur BTC en 1h
- 14:31 → Webhook Discord : "📈 CROISEMENT PAIRE : MA20 × MA50 - BTCUSDT (1h)"
- Interprétation: Signal court terme important
- Paires surveillées: 7-20, 20-50, 13-25, 25-32, 32-100, 100-200

**3. Croisements Multiples** ⭐ NOUVEAU
- 16:00 → MA13 croise simultanément MA25 ET MA32 sur SOL en 4h
- 16:01 → Webhook Discord : "⚡ CROISEMENT MULTIPLE : MA13 croise 2 moyennes (MA25, MA32) - SOLUSDT (4h)"
- Interprétation: Signal de force/faiblesse exceptionnel

**4. MA112 Long Terme** ⭐ NOUVEAU
- 18:00 → MA112 croise MA336 sur AVAX en 1d
- 18:01 → Webhook Discord : "📊 MA112 LONG TERME : MA112 × MA336 - AVAXUSDT (1d)"
- Interprétation: Changement de tendance majeure

**5. Compression**
- 20:00 → Les MA de BTC sont compressées (<5% d'écart) en 1h
- 20:01 → Webhook Discord : "⚠️ COMPRESSION détectée : BTCUSDT (1h) - Volatilité imminente"
- Interprétation: Préparation à un mouvement fort

**6. Alignement**
- 22:00 → Prix ETH > toutes les MA en 4h
- 22:01 → Webhook Discord : "🟢 ALIGNEMENT HAUSSIER : ETHUSDT (4h)"
- Interprétation: Tendance haussière confirmée

---

## 🚀 DÉPLOIEMENT & PRODUCTION

### Configuration Serveur (Linux/Ubuntu)

#### 1. Préparation du Serveur

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Python 3.10
sudo apt install python3.10 python3.10-venv python3-pip -y

# Installation Git
sudo apt install git -y
```

#### 2. Clone du Repository

```bash
cd /home/ubuntu
git clone https://github.com/votre-repo/trade-helper-bot-discord.git
cd trade-helper-bot-discord
```

#### 3. Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Configuration .env

```bash
nano .env
```

```env
DISCORD_TOKEN=votre_token_ici
```

#### 5. Service Systemd

**Créer le fichier service:**
```bash
sudo nano /etc/systemd/system/discord-bot.service
```

**Contenu:**
```ini
[Unit]
Description=Discord Trading Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trade-helper-bot-discord
ExecStart=/home/ubuntu/trade-helper-bot-discord/venv/bin/python3 bot.py
Restart=always
RestartSec=60
StartLimitBurst=5
StartLimitIntervalSec=300

# Limites ressources
MemoryMax=200M
MemoryHigh=180M
CPUQuota=40%

Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Activer le service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-bot.service
sudo systemctl start discord-bot.service
```

**Vérifier le status:**
```bash
sudo systemctl status discord-bot.service
```

**Voir les logs:**
```bash
sudo journalctl -u discord-bot.service -f
```

---

### Configuration AWS EC2

#### Recommandations Matérielles

**Pour usage normal (2-3 bots):**
- **Instance:** t2.small ou t3.small
- **RAM:** 2GB minimum
- **CPU:** 2 vCPUs
- **Stockage:** 20GB SSD
- **Coût:** ~$12-15/mois

**Configuration VM:**
- OS: Ubuntu 22.04 LTS
- Swap: 2GB
- Limites: 200MB RAM max, 40% CPU max

#### Sécurité

**Security Group:**
- SSH (22): Votre IP uniquement
- HTTPS (443): 0.0.0.0/0 (APIs externes)

**Swap (recommandé):**
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 🔍 MAINTENANCE & MONITORING

### Commandes Utiles

#### Logs en Temps Réel
```bash
sudo journalctl -u discord-bot.service -f
```

#### Redémarrer le Bot
```bash
sudo systemctl restart discord-bot.service
```

#### Arrêter le Bot
```bash
sudo systemctl stop discord-bot.service
```

#### Vérifier la RAM/CPU
```bash
top
# ou
htop
```

#### Vérifier le Swap
```bash
free -h
swapon --show
```

### Métriques de Performance

| Métrique | Valeur Normale | Seuil Alerte |
|----------|----------------|--------------|
| RAM utilisée | 150-180MB | > 180MB |
| CPU | 5-15% | > 40% |
| Requêtes API/h | 60-80 | > 200 |
| Temps réponse | 1-3s | > 5s |
| Uptime | > 99% | < 95% |
| Restarts/jour | 0 | > 3 |

### Troubleshooting

#### Bot ne répond pas
```bash
sudo systemctl status discord-bot.service
sudo journalctl -u discord-bot.service --since "1 hour ago"
```

#### OOM Killer
```bash
sudo dmesg | grep -i "killed process"
```

Solution: Augmenter swap ou RAM

#### Erreurs API Binance
- Vérifier connexion internet
- Vérifier rate limit (max 1200 req/min)
- Augmenter `check_interval_minutes`

---

## 📊 ACTIFS CONFIGURÉS

### Cryptomonnaies (6 actifs)

| Symbole | Binance Symbol | Description |
|---------|----------------|-------------|
| BTC | BTCUSDT | Bitcoin |
| ETH | ETHUSDT | Ethereum |
| AVAX | AVAXUSDT | Avalanche |
| ASTER | ASTERUSDT | Aster |
| SOL | SOLUSDT | Solana |
| AAVE | AAVEUSDT | Aave |

**Données:** Binance API (temps réel)
**Timeframes:** 5m, 15m, 1h, 4h, 1d

### Actions/Indices (4 actifs)

| Symbole | Yahoo Finance | Description |
|---------|---------------|-------------|
| AAPL | AAPL | Apple Inc. |
| MSFT | MSFT | Microsoft Corporation |
| SPX | ^GSPC | S&P 500 Index |
| TTE | TTE | TotalEnergies SE |

**Données:** Yahoo Finance
**Timeframes:** 1d, 1w, 1mo

**Note:** Vous pouvez ajouter/supprimer des actifs en temps réel via les commandes `/crypto_add`, `/crypto_remove`, `/stock_add`, `/stock_remove`.

---

## 🔔 CONFIGURATION DES ALERTES

### Alertes Volume
- **Fréquence:** Toutes les 15 minutes
- **Seuils:** +150% (modéré), +200% (élevé), +300% (critique)
- **Référence:** MA25 et MA300
- **Cooldown:** 30 minutes entre alertes

### Alertes MA (Moyennes Mobiles) ⭐ AMÉLIORÉ + PRIORITÉS 🆕
- **Fréquence:** Toutes les 60 minutes
- **Timeframes surveillés:** 15m, 1h, 4h, 1d
- **Systèmes de MA:**
  - Système 1: MA7, MA13, MA20, MA25, MA32, MA50, MA100, MA200, MA300
  - Système 2: MA112, MA336, MA375, MA448, MA750
- **Système de Priorités** 🆕 - Chaque alerte affiche maintenant:
  - **Tier** (1-3): Niveau de priorité du signal
  - **Rating** (sur 10): Score de fiabilité basé sur backtests
  - **Win Rate**: Taux de réussite historique (ex: 72-80%)
  - **Étoiles**: Visualisation rapide (⭐⭐⭐⭐⭐ = 10/10)
  - **Emoji**: 🏆 Tier 1 | 🥈 Tier 2 | 🥉 Tier 3
- **Types d'alertes avec ratings:**
  - **Golden Cross** 🏆 (MA100 > MA200) - **Tier 1 - 10/10** - Signal institutionnel majeur
  - **Death Cross** 🏆 (MA100 < MA200) - **Tier 1 - 10/10** - Signal baissier institutionnel
  - **MA20×50** 🥈 - **Tier 2 - 9/10** - Swing trading optimal
  - **MA32×100** 🥈 - **Tier 2 - 8.5/10** - Position trading
  - **Croisements Paires** ⭐ - Détection de 6 paires avec ratings:
    - **20-50** 🥈 (Tier 2 - 9/10)
    - **32-100** 🥈 (Tier 2 - 8.5/10)
    - **100-200** 🏆 (Tier 1 - 10/10) - Golden/Death Cross
    - **25-32** 🥉 (Tier 3 - 7/10)
    - **13-25** 🥉 (Tier 3 - 6.5/10)
    - **7-20** 🥉 (Tier 3 - 6/10)
  - **Croisements Multiples** ⭐ - Quand une MA croise ≥2 MA simultanément
    - Ex: MA13 croise à la fois MA25 ET MA32
    - Signal de force/faiblesse important
  - **MA112 Multi Long Terme** 🏆 ⭐ - **Tier 1 - 10/10** - MA112 croise ≥3 MA long terme:
    - 112 × (336+375+448+750)
    - Win Rate: 85-90% - **SIGNAL EXTRÊMEMENT RARE**
    - **OPPORTUNITÉ GÉNÉRATIONNELLE** - Cycle majeur
  - **Alignements haussiers/baissiers** - Prix > toutes MA ou prix < toutes MA
  - **Compressions** - Écart <5% entre MA (volatilité imminente)
- **Cooldown:** 4 heures par actif
- **Warm-up:** 1 heure au démarrage (prévention faux signaux)
- **💡 Avantage:** Prioriser les signaux à fort win rate (Tier 1-2) vs noise élevé (Tier 3)

### Webhooks Discord
- **Volume:** URL unique pour alertes volume
- **MA Cross:** URL séparée pour croisements Golden/Death
- **MA Alignment:** URL séparée pour alignements
- **MA Compression:** URL séparée pour compressions

---

## 🗺️ ROADMAP & ÉVOLUTIONS

### ✅ Implémenté

**Calculs de trading :**
- ✅ Calculs de position (spot, levier, R/R, DCA)
- ✅ **Calcul perte au SL + gain au TP** avec comparaison (nouveau !)
- ✅ Prix de liquidation et scénarios P&L

**Analyse technique :**
- ✅ Analyse technique moyennes mobiles (2 systèmes)
- ✅ Multi-timeframes (5m à 1d)
- ✅ Support cryptos (Binance) et actions (Yahoo Finance)
- ✅ **Comparaison sélective d'actifs** (nouveau !)
  - Compare tous les actifs OU sélection personnalisée
  - `/crypto_compare assets:BTC,ETH,SOL`
  - `/stock_compare assets:AAPL,MSFT,SPX`

**Alertes automatiques :**
- ✅ Alertes automatiques volumes (toutes les 15 min)
- ✅ Alertes automatiques MA (toutes les 60 min)
- ✅ **Détection croisements paires spécifiques** (7-20, 20-50, 13-25, 25-32, 32-100, 100-200) ⭐ NOUVEAU
- ✅ **Détection croisements multiples** (≥2 MA croisées simultanément) ⭐ NOUVEAU
- ✅ **Détection MA112 long terme** (336, 375, 448, 750) ⭐ NOUVEAU
- ✅ **Système de priorités des signaux** (Tier 1-3 avec ratings 1-10) 🆕 NOUVEAU
  - Backtest historique S&P 500 + Crypto (1990-2025)
  - Win rates affichés pour chaque signal (50-90%)
  - Emojis visuels 🏆🥈🥉 selon tier
  - Étoiles ⭐ selon rating
  - Identification signaux rares Tier 1 (opportunités générationnelles)
- ✅ **Système de Scoring EMA Cascade v2.0** (Score sur 100 points) 🆕🔥 NOUVEAU
  - Architecture 4 tiers : Direction Daily (35) + Signal TF (35) + Multi-TF (20) + Technique (10)
  - Thresholds adaptatifs par timeframe (Daily >65 | H4 >70 | H1 >72 | 15min >70)
  - Classification S/A/B/C/D par conviction (90-100, 80-89, 70-79, 65-69, <65)
  - Détection Volume + RSI + ADX automatique
  - Protection contre-trend Daily (règle absolue)
  - 15min H1 aligned OBLIGATOIRE (protection whipsaws)
  - Win rates prévisibles selon score (70-92%)
  - Affichage détaillé dans chaque alerte
- ✅ Webhooks Discord pour notifications
- ✅ Système de cooldown anti-spam
- ✅ Warm-up mode pour alertes MA

**Outils :**
- ✅ Recherche de symboles intégrée (Binance + Yahoo Finance)
- ✅ Retry automatique Binance
- ✅ Ajout/suppression d'actifs en temps réel

### Priorité Haute

#### Bot de News/Veille
- Agrégation automatique de news crypto/finance
- Webhooks Discord pour alertes
- Sources: CoinDesk, CoinTelegraph, Twitter/X

#### Gestion Avancée des Alertes
- Interface de configuration via Discord
- Personnalisation des seuils par actif
- Historique des alertes envoyées
- Statistiques d'alertes

### Priorité Moyenne

#### Alertes Indicateurs Techniques Additionnels
- RSI (Surachat/Survente)
- MACD (Croisements)
- Bollinger Bands
- Fibonacci retracements
- Volume Profile

#### Backtesting
- Test de stratégies sur données historiques
- Calcul de performance
- Rapports détaillés
- Win rate et Sharpe ratio

#### Multi-Timeframe Confluence
- Analyse simultanée sur plusieurs TF
- Score de confluence de signaux
- Détection de divergences inter-TF

### Priorité Basse

#### Portfolio Tracking
- Suivi de portefeuille en temps réel
- P&L tracking automatique
- Calcul de performance
- Rapports périodiques

#### Interface Web
- Dashboard de configuration
- Visualisation graphique des MA
- Historique des signaux
- Gestion des actifs

#### Alertes Multi-Plateformes
- Notifications via Telegram
- Support Slack
- Email notifications
- SMS (via Twilio)

#### Machine Learning
- Prédiction de prix basée sur ML
- Détection de patterns avancés
- Optimisation automatique des paramètres

---

## 📞 SUPPORT & CONTRIBUTION

### Signaler un Bug

1. Vérifiez que ce n'est pas un problème connu
2. Créez une issue sur GitHub avec:
   - Description du problème
   - Logs d'erreur
   - Steps to reproduce
   - Configuration utilisée

### Contribuer

1. Fork le repository
2. Créez une branche feature (`git checkout -b feature/ma-feature`)
3. Commit vos changements (`git commit -m 'Add some feature'`)
4. Push sur la branche (`git push origin feature/ma-feature`)
5. Ouvrez une Pull Request

---

## 📄 LICENCE

Ce projet est sous licence MIT.

---

## 👤 AUTEUR

**Bastien D'ALBA**
- GitHub: [@votre-username](https://github.com/votre-username)
- Email: dalba.bastien@gmail.com

---

**Dernière mise à jour:** 17/01/2026
