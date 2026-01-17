[Documentation_TradeHelperBot_2026-01-17.md](https://github.com/user-attachments/files/24688844/Documentation_TradeHelperBot_2026-01-17.md)
# 📚 DOCUMENTATION - Trade Helper Bot Discord

**Version:** 1.0  
**Date:** 17/01/2026  
**Repository:** trade-helper-bot-discord  
**Auteur:** Bastien D'ALBA

---

## 📋 TABLEQuest DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation & Configuration](#installation--configuration)
4. [Commandes Disponibles](#commandes-disponibles)
5. [Modules Techniques](#modules-techniques)
6. [Déploiement & Production](#déploiement--production)
7. [Maintenance & Monitoring](#maintenance--monitoring)
8. [Roadmap & Évolutions](#roadmap--évolutions)

---

## 🎯 VUE D'ENSEMBLE

### Description

**Trade Helper Bot** est un bot Discord en Python conçu pour assister les traders dans leurs calculs de position et l'analyse technique des cryptomonnaies et actions.

### Fonctionnalités Principales

#### 💼 Calculs de Trading
- **Calcul de position spot** : Dimensionnement optimal selon le risque
- **Calcul avec levier** : Gestion du risque avec effet de levier (Futures/Margin)
- **Ratio Risk/Reward** : Calcul automatique du R/R
- **DCA (Dollar Cost Averaging)** : Prix moyen d'achat

#### 📊 Analyse Technique
- **Moyennes Mobiles (MA)** : Système double MA (court & long terme)
- **Détection de croisements** : Golden Cross, Death Cross, croisements multiples
- **Compression des MA** : Détection de volatilité imminente
- **Position du prix** : Prix vs toutes les MA

#### 🔧 Gestion Dynamique
- **Ajout/Suppression de cryptos** : Gestion en temps réel
- **Validation Binance** : Vérification automatique des symboles
- **Multi-timeframes** : 5m, 15m, 1h, 4h, 1d

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
├── bot.py                    # Point d'entrée principal
├── market_analysis.py        # Analyseur de marché Binance
├── crypto_manager.py         # Gestionnaire de cryptos
├── stock_manager.py          # Gestionnaire d'actions
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
- Gestion des commandes slash
- Orchestration des modules

**Imports principaux:**
```python
import discord
from discord.ext import commands
from market_analysis import BinanceMarketAnalyzer
from crypto_manager import CryptoManager
```

#### 2. **market_analysis.py**
- Classe `BinanceMarketAnalyzer`
- Connexion API Binance
- Calcul des moyennes mobiles
- Détection de signaux

**Fonctionnalités:**
- `analyze_symbol()` - Analyse complète d'un actif
- `get_ma_values()` - Calcul des MA
- `detect_crossovers()` - Détection croisements
- `test_symbol_exists()` - Validation Binance

#### 3. **crypto_manager.py**
- Classe `CryptoManager`
- Gestion du fichier cryptos.json
- Validation des symboles Binance

**Méthodes:**
- `add_crypto()` - Ajouter une crypto
- `remove_crypto()` - Supprimer une crypto
- `get_all_cryptos()` - Lister toutes
- `crypto_exists()` - Vérifier existence

### Système de Moyennes Mobiles

#### Système 1 (Court/Moyen Terme)
```
MA13, MA25, MA32, MA50, MA100, MA200, MA300
```

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
| **Alignement Haussier** | Prix > toutes MA | 🟢 Tendance haussière |
| **Alignement Baissier** | Prix < toutes MA | 🔴 Tendance baissière |
| **Compression** | Écart MA < 5% | ⚠️ Volatilité imminente |

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
  "ETH": "ETHUSDT"
}
```

**stocks.json:**
```json
{
  "AAPL": "AAPL",
  "MSFT": "MSFT"
}
```

**ma_alerts_config.json:**
```json
{
  "check_interval_minutes": 360,
  "cooldown_hours": 6,
  "compression_threshold": 3.0,
  "assets": {
    "crypto": ["BTCUSDT", "ETHUSDT"],
    "stocks": []
  },
  "timeframes": ["1d"],
  "alert_types": {
    "golden_cross": true,
    "death_cross": true,
    "alignment": false,
    "compression": false
  }
}
```

**volume_config.json:**
```json
{
  "check_interval_minutes": 120,
  "cooldown_minutes": 120,
  "thresholds": {
    "moderate": 200,
    "high": 300,
    "critical": 400
  },
  "reference_periods": {
    "short": 25,
    "long": 300
  },
  "assets": {
    "crypto": ["BTCUSDT", "ETHUSDT"],
    "stocks": []
  }
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
**Description:** Calcule une position avec effet de levier (Futures)

**Paramètres:**
- `capital` (obligatoire) : Capital disponible
- `leverage` (obligatoire) : Levier (2x, 5x, 10x, 20x, 50x, 100x)
- `risk_percent` (obligatoire) : % de risque
- `entry` (obligatoire) : Prix d'entrée
- `stop_loss` (obligatoire) : Stop loss
- `target` (optionnel) : Prix cible

**Exemple:**
```
/leverage capital:1000 leverage:10 risk_percent:2 entry:50 stop_loss:49 target:52
```

**Résultat:**
- Marge requise
- Exposition totale
- Prix de liquidation
- Distance à la liquidation
- P&L au stop/target
- Ratio R/R
- ⚠️ Avertissements de sécurité

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
**Description:** Comparer toutes les cryptos configurées

**Paramètres:**
- `timeframe` (optionnel) : 1d par défaut

**Résultat:**
- Vue d'ensemble de toutes les cryptos
- Status de chacune
- Alertes de compression

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
- `terme` : Terme de recherche

---

### Catégorie 3: Analyse Actions (Yahoo Finance)

#### /stock_check
**Description:** Analyser les moyennes mobiles d'une action

**Paramètres:**
- `stock` : Symbole (AAPL, MSFT, TSLA...)
- `timeframe` : 1d, 1w, 1mo

---

#### /stock_compare
**Description:** Comparer toutes les actions configurées

---

#### /stock_list
**Description:** Lister toutes les actions supportées

---

#### /stock_add / /stock_remove / /stock_search
*Fonctionnent comme les commandes crypto équivalentes*

---

### Catégorie 4: Configuration & Aide

#### /help
**Description:** Afficher toutes les commandes disponibles

**Résultat:**
- Guide complet des commandes
- Explications détaillées
- Exemples d'utilisation

---

#### /ma_alerts_config
**Description:** Voir la configuration des alertes MA

---

#### /volume_config
**Description:** Voir la configuration des alertes volume

---

## 🔧 MODULES TECHNIQUES

### BinanceMarketAnalyzer

**Localisation:** `market_analysis.py`

**Responsabilités:**
- Connexion à l'API Binance
- Récupération des données OHLCV
- Calcul des moyennes mobiles
- Détection de signaux techniques

**Méthodes Principales:**

```python
class BinanceMarketAnalyzer:
    def __init__(self):
        self.client = Client()  # Client Binance public
        
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
        """Calcule les moyennes mobiles"""
        
    def detect_crossovers(self, current_ma: dict, previous_ma: dict) -> list:
        """Détecte les croisements de MA"""
        
    def test_symbol_exists(self, symbol: str) -> bool:
        """Vérifie si un symbole existe sur Binance"""
```

---

### CryptoManager

**Localisation:** `crypto_manager.py`

**Responsabilités:**
- Gestion du fichier cryptos.json
- CRUD des cryptos
- Validation des symboles

**Méthodes Principales:**

```python
class CryptoManager:
    def __init__(self, file_path: str = 'cryptos.json'):
        self.file_path = file_path
        self.cryptos = self._load_cryptos()
        
    def add_crypto(self, symbol: str, binance_symbol: str) -> bool:
        """Ajoute une crypto"""
        
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
```

**Format cryptos.json:**
```json
{
  "BTC": "BTCUSDT",
  "ETH": "ETHUSDT",
  "SOL": "SOLUSDT"
}
```

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

## 🗺️ ROADMAP & ÉVOLUTIONS

### Priorité Haute

#### Bot de News/Veille
- Agrégation automatique de news crypto/finance
- Webhooks Discord pour alertes
- Sources: CoinDesk, CoinTelegraph, Twitter

### Priorité Moyenne

#### Alertes Indicateurs Techniques
- RSI (Surachat/Survente)
- MACD (Croisements)
- Bollinger Bands
- Fibonacci retracements

#### Backtesting
- Test de stratégies sur données historiques
- Calcul de performance
- Rapports détaillés

### Priorité Basse

#### Multi-Timeframe Analysis
- Analyse simultanée sur plusieurs TF
- Confluence de signaux
- Score de confiance

#### Portfolio Tracking
- Suivi de portefeuille en temps réel
- P&L tracking
- Calcul de performance

#### Interface Web
- Dashboard de configuration
- Visualisation des alertes
- Historique des signaux

#### Alertes Telegram
- Notifications via Telegram
- Multi-canal
- Personnalisation

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
