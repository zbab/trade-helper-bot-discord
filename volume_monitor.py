from binance.client import Client
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import requests

class VolumeMonitor:
    """Surveillance des volumes avec détection de pics"""
    
    def __init__(self, config_file: str = "volume_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.binance_client = Client()
        self.alert_history = {}  # {symbol: last_alert_timestamp}
        
        # Périodes de moyennes mobiles pour le volume
        self.volume_ma_periods = [13, 25, 32, 100, 200, 300]
        
    def _load_config(self) -> Dict:
        """Charge la configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Configuration par défaut
            default_config = {
                "check_interval_minutes": 15,
                "webhook_url": "",
                "cooldown_minutes": 30,
                "thresholds": {
                    "moderate": 150,
                    "high": 200,
                    "critical": 300
                },
                "reference_periods": {
                    "short": 25,   # MA25 comme référence court terme
                    "long": 300    # MA300 comme référence long terme
                },
                "assets": {
                    "crypto": ["BTCUSDT", "ETHUSDT"],
                    "stocks": ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA"]
                }
            }
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict = None):
        """Sauvegarde la configuration"""
        if config is None:
            config = self.config
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def set_webhook_url(self, webhook_url: str):
        """Configure l'URL du webhook Discord"""
        self.config['webhook_url'] = webhook_url
        self._save_config()
    
    def _can_send_alert(self, symbol: str) -> bool:
        """Vérifie si on peut envoyer une alerte (cooldown)"""
        if symbol not in self.alert_history:
            return True
        
        last_alert = self.alert_history[symbol]
        cooldown_seconds = self.config['cooldown_minutes'] * 60
        time_since_last = (datetime.now() - last_alert).total_seconds()
        
        return time_since_last >= cooldown_seconds
    
    def _mark_alert_sent(self, symbol: str):
        """Marque qu'une alerte a été envoyée"""
        self.alert_history[symbol] = datetime.now()
    
    def get_crypto_volume_data(self, symbol: str) -> Optional[Dict]:
        """Récupère les données de volume crypto (Binance)"""
        try:
            # Récupérer suffisamment de bougies pour calculer les MA + volume actuel
            max_period = max(self.volume_ma_periods)
            klines_all = self.binance_client.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1HOUR,
                limit=max_period + 2  # +2 pour avoir la bougie actuelle
            )
            
            # Volume et prix de la dernière bougie COMPLÈTE (avant-dernière)
            last_complete_candle = klines_all[-2]
            current_volume = float(last_complete_candle[5])  # Volume
            current_price = float(last_complete_candle[4])   # Close
            
            # Calculer les moyennes mobiles du volume (exclure la bougie en cours)
            volume_mas = {}
            volumes_history = [float(k[5]) for k in klines_all[:-1]]  # Toutes sauf la dernière
            
            for period in self.volume_ma_periods:
                if len(volumes_history) >= period:
                    # Prendre les N dernières valeurs
                    recent_volumes = volumes_history[-period:]
                    volume_mas[f'ma{period}'] = sum(recent_volumes) / len(recent_volumes)
                else:
                    volume_mas[f'ma{period}'] = sum(volumes_history) / len(volumes_history)
            
            # Références : MA25 pour court terme, MA300 pour long terme
            avg_volume_short = volume_mas.get('ma25', current_volume)
            avg_volume_long = volume_mas.get('ma300', current_volume)
            
            # Calcul des augmentations
            increase_short = 0
            increase_long = 0
            
            if avg_volume_short > 0:
                increase_short = ((current_volume - avg_volume_short) / avg_volume_short) * 100
            
            if avg_volume_long > 0:
                increase_long = ((current_volume - avg_volume_long) / avg_volume_long) * 100
            
            return {
                'symbol': symbol,
                'type': 'crypto',
                'current_volume': current_volume,
                'current_price': current_price,
                'avg_volume_24h': avg_volume_short,
                'avg_volume_7d': avg_volume_long,
                'volume_ma13': volume_mas.get('ma13', 0),
                'volume_ma25': volume_mas.get('ma25', 0),
                'volume_ma32': volume_mas.get('ma32', 0),
                'volume_ma100': volume_mas.get('ma100', 0),
                'volume_ma200': volume_mas.get('ma200', 0),
                'volume_ma300': volume_mas.get('ma300', 0),
                'increase_24h': increase_short,
                'increase_7d': increase_long,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Erreur crypto {symbol}: {e}")
            return None
    
    def get_stock_volume_data(self, symbol: str) -> Optional[Dict]:
        """Récupère les données de volume stock (Yahoo Finance)"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Données 1h sur période suffisante pour MA300
            df = ticker.history(period="60d", interval="1h")
            
            if df.empty or len(df) < 25:
                return None
            
            df.columns = df.columns.str.lower()
            
            # Volume actuel (dernière bougie)
            current_volume = df['volume'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Calculer les moyennes mobiles du volume : MA13, MA25, MA32, MA100, MA200, MA300
            volume_mas = {}
            
            for period in self.volume_ma_periods:
                if len(df) >= period + 1:
                    # Exclure la bougie en cours
                    volume_mas[f'ma{period}'] = df['volume'].iloc[-period-1:-1].mean()
                else:
                    # Si pas assez de données, utiliser ce qu'on a
                    volume_mas[f'ma{period}'] = df['volume'].iloc[:-1].mean()
            
            # Références : MA25 pour court terme, MA300 pour long terme
            avg_volume_short = volume_mas.get('ma25', current_volume)
            avg_volume_long = volume_mas.get('ma300', current_volume)
            
            # Calcul des augmentations
            increase_short = 0
            increase_long = 0
            
            if avg_volume_short > 0:
                increase_short = ((current_volume - avg_volume_short) / avg_volume_short) * 100
            
            if avg_volume_long > 0:
                increase_long = ((current_volume - avg_volume_long) / avg_volume_long) * 100
            
            return {
                'symbol': symbol,
                'type': 'stock',
                'current_volume': current_volume,
                'current_price': current_price,
                'avg_volume_24h': avg_volume_short,  # MA25
                'avg_volume_7d': avg_volume_long,    # MA300
                'volume_ma13': volume_mas.get('ma13', 0),
                'volume_ma25': volume_mas.get('ma25', 0),
                'volume_ma32': volume_mas.get('ma32', 0),
                'volume_ma100': volume_mas.get('ma100', 0),
                'volume_ma200': volume_mas.get('ma200', 0),
                'volume_ma300': volume_mas.get('ma300', 0),
                'increase_24h': increase_short,
                'increase_7d': increase_long,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Erreur stock {symbol}: {e}")
            return None
    
    def detect_spike(self, data: Dict) -> Optional[str]:
        """Détecte un pic de volume et retourne le niveau d'alerte"""
        if not data:
            return None
        
        # On utilise l'augmentation vs MA25 (court terme) comme référence principale
        increase = data['increase_24h']
        thresholds = self.config['thresholds']
        
        if increase >= thresholds['critical']:
            return 'critical'
        elif increase >= thresholds['high']:
            return 'high'
        elif increase >= thresholds['moderate']:
            return 'moderate'
        
        return None
    
    def send_discord_alert(self, data: Dict, alert_level: str):
        """Envoie une alerte sur Discord via webhook - VERSION 1 : CLAIR ET FACTUEL"""
        webhook_url = self.config.get('webhook_url')
        
        if not webhook_url:
            print("⚠️  Webhook URL non configurée")
            return
        
        if not self._can_send_alert(data['symbol']):
            print(f"⏳ Cooldown actif pour {data['symbol']}")
            return
        
        # Configuration par niveau d'alerte
        emoji_map = {
            'moderate': '⚠️',
            'high': '🔥',
            'critical': '🚨'
        }
        
        color_map = {
            'moderate': 0xFFA500,  # Orange
            'high': 0xFF4500,      # Rouge-orange
            'critical': 0xFF0000   # Rouge
        }
        
        level_text = {
            'moderate': 'MODÉRÉ (+150%)',
            'high': 'ÉLEVÉ (+200%)',
            'critical': 'CRITIQUE (+300%)'
        }
        
        emoji = emoji_map.get(alert_level, '📊')
        color = color_map.get(alert_level, 0x3498db)
        level_name = level_text.get(alert_level, 'ALERTE')
        
        # Formater le symbole
        symbol_display = data['symbol'].replace('USDT', '').replace('BUSD', '')
        
        # Lien vers la plateforme
        if data['type'] == 'crypto':
            link = f"https://www.binance.com/en/trade/{data['symbol']}"
        else:
            link = f"https://finance.yahoo.com/quote/{data['symbol']}"
        
        # Construire l'embed Discord
        embed = {
            "title": f"{emoji} PIC DE VOLUME - {symbol_display}",
            "description": f"**Niveau : {level_name}**",
            "color": color,
            "url": link,
            "fields": [
                {
                    "name": "━━━━━━━━━━━━━━━━━━━━━━",
                    "value": "** **",
                    "inline": False
                },
                {
                    "name": "📊 SITUATION ACTUELLE",
                    "value": (
                        f"**Volume actuel:** {data['current_volume']:,.0f}\n"
                        f"**Prix actuel:** ${data['current_price']:,.2f}\n"
                        f"**Heure:** {data['timestamp'].strftime('%H:%M:%S')}"
                    ),
                    "inline": False
                },
                {
                    "name": "━━━━━━━━━━━━━━━━━━━━━━",
                    "value": "** **",
                    "inline": False
                },
                {
                    "name": "📈 COMPARAISON COURT TERME (MA25 - ~1 jour)",
                    "value": (
                        f"**Moyenne normale:** {data['avg_volume_24h']:,.0f}\n"
                        f"**Volume actuel:** {data['current_volume']:,.0f}\n"
                        f"**Variation:** {data['increase_24h']:+.1f}%"
                    ),
                    "inline": False
                },
                {
                    "name": "📉 COMPARAISON LONG TERME (MA300 - ~12 jours)",
                    "value": (
                        f"**Moyenne normale:** {data['avg_volume_7d']:,.0f}\n"
                        f"**Volume actuel:** {data['current_volume']:,.0f}\n"
                        f"**Variation:** {data['increase_7d']:+.1f}%"
                    ),
                    "inline": False
                },
                {
                    "name": "━━━━━━━━━━━━━━━━━━━━━━",
                    "value": "** **",
                    "inline": False
                },
                {
                    "name": "📊 DÉTAIL DES MOYENNES MOBILES",
                    "value": (
                        f"MA13 (13h):  `{data['volume_ma13']:>12,.0f}`\n"
                        f"MA25 (1j):   `{data['volume_ma25']:>12,.0f}`\n"
                        f"MA32 (32h):  `{data['volume_ma32']:>12,.0f}`\n"
                        f"MA100 (4j):  `{data['volume_ma100']:>12,.0f}`\n"
                        f"MA200 (8j):  `{data['volume_ma200']:>12,.0f}`\n"
                        f"MA300 (12j): `{data['volume_ma300']:>12,.0f}`"
                    ),
                    "inline": False
                }
            ],
            "footer": {
                "text": f"{data['type'].upper()} • Alerte {level_name}"
            },
            "timestamp": data['timestamp'].isoformat()
        }
        
        payload = {"embeds": [embed]}
        
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 204:
                print(f"✅ Alerte envoyée pour {data['symbol']}")
                self._mark_alert_sent(data['symbol'])
            else:
                print(f"❌ Erreur webhook: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur envoi webhook: {e}")
    
    def check_all_assets(self) -> List[Dict]:
        """Vérifie tous les actifs et envoie des alertes si nécessaire"""
        alerts_sent = []
        
        # Vérifier cryptos
        for crypto in self.config['assets']['crypto']:
            data = self.get_crypto_volume_data(crypto)
            if data:
                alert_level = self.detect_spike(data)
                if alert_level:
                    self.send_discord_alert(data, alert_level)
                    alerts_sent.append({
                        'symbol': crypto,
                        'level': alert_level,
                        'increase': data['increase_24h']
                    })
        
        # Vérifier stocks
        for stock in self.config['assets']['stocks']:
            data = self.get_stock_volume_data(stock)
            if data:
                alert_level = self.detect_spike(data)
                if alert_level:
                    self.send_discord_alert(data, alert_level)
                    alerts_sent.append({
                        'symbol': stock,
                        'level': alert_level,
                        'increase': data['increase_24h']
                    })
        
        return alerts_sent
    
    def get_current_status(self) -> Dict:
        """Récupère l'état actuel de tous les actifs"""
        status = {
            'crypto': [],
            'stocks': []
        }
        
        for crypto in self.config['assets']['crypto']:
            data = self.get_crypto_volume_data(crypto)
            if data:
                status['crypto'].append(data)
        
        for stock in self.config['assets']['stocks']:
            data = self.get_stock_volume_data(stock)
            if data:
                status['stocks'].append(data)
        
        return status