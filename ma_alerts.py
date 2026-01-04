from binance.client import Client
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
import requests

class MAAlertMonitor:
    """Surveillance des croisements et alignements de moyennes mobiles"""
    
    def __init__(self, config_file: str = "ma_alerts_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.binance_client = Client()
        self.alert_history = {}  # Pour éviter spam
        
        # Deux systèmes de MA
        self.ma_system1 = [13, 25, 32, 50, 100, 200, 300]  # Court terme
        self.ma_system2 = [112, 336, 375, 448, 750]    # Long terme
        
        # État précédent pour détecter les croisements
        self.previous_state = {}
        
    def _load_config(self) -> Dict:
        """Charge la configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            default_config = {
                "check_interval_minutes": 60,
                "webhook_url": "",
                "cooldown_hours": 4,
                "compression_threshold": 3.0,
                "assets": {
                    "crypto": ["BTCUSDT", "ETHUSDT"],
                    "stocks": ["AAPL", "MSFT", "NVDA", "TSLA"]
                },
                "timeframes": ["4h", "1d"],
                "alert_types": {
                    "golden_cross": True,
                    "death_cross": True,
                    "alignment": True,
                    "compression": True
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
    
    def set_webhook_url(self, webhook_url: str, alert_type: str = 'all'):
        """
        Configure l'URL d'un webhook
        
        Args:
            webhook_url: URL du webhook
            alert_type: Type d'alerte ('cross', 'alignment', 'compression', ou 'all')
        """
        if 'webhooks' not in self.config:
            self.config['webhooks'] = {}
        
        if alert_type == 'all':
            self.config['webhooks']['cross'] = webhook_url
            self.config['webhooks']['alignment'] = webhook_url
            self.config['webhooks']['compression'] = webhook_url
        else:
            self.config['webhooks'][alert_type] = webhook_url
        
        self._save_config()

    def _can_send_alert(self, alert_key: str) -> bool:
        """Vérifie cooldown (éviter spam)"""
        if alert_key not in self.alert_history:
            return True
        
        last_alert = self.alert_history[alert_key]
        cooldown_seconds = self.config['cooldown_hours'] * 3600
        time_since = (datetime.now() - last_alert).total_seconds()
        
        return time_since >= cooldown_seconds
    
    def _mark_alert_sent(self, alert_key: str):
        """Marque qu'une alerte a été envoyée"""
        self.alert_history[alert_key] = datetime.now()
    
    def get_crypto_ma_data(self, symbol: str, timeframe: str, ma_system: List[int]) -> Optional[Dict]:
        """Récupère les MA pour une crypto"""
        try:
            interval_map = {
                '5m': Client.KLINE_INTERVAL_5MINUTE,
                '15m': Client.KLINE_INTERVAL_15MINUTE,
                '1h': Client.KLINE_INTERVAL_1HOUR,
                '4h': Client.KLINE_INTERVAL_4HOUR,
                '1d': Client.KLINE_INTERVAL_1DAY,
            }
            
            binance_interval = interval_map.get(timeframe, Client.KLINE_INTERVAL_1DAY)
            limit = max(ma_system) + 50
            
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=binance_interval,
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['close'] = df['close'].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculer les MA
            ma_values = {}
            for period in ma_system:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
                ma_values[period] = df[f'MA{period}'].iloc[-1]
            
            current_price = df['close'].iloc[-1]
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_price': current_price,
                'ma_values': ma_values,
                'df': df,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Erreur crypto MA {symbol}: {e}")
            return None
    
    def get_stock_ma_data(self, symbol: str, timeframe: str, ma_system: List[int]) -> Optional[Dict]:
        """Récupère les MA pour une action"""
        try:
            ticker = yf.Ticker(symbol)
            
            interval_map = {
                '1h': '1h',
                '4h': '1h',
                '1d': '1d'
            }
            
            period_map = {
                '1h': '60d',
                '4h': '60d',
                '1d': 'max'
            }
            
            yf_interval = interval_map.get(timeframe, '1d')
            period = period_map.get(timeframe, 'max')
            
            df = ticker.history(period=period, interval=yf_interval)
            
            if df.empty:
                return None
            
            df.columns = df.columns.str.lower()
            
            # Resample pour 4h si nécessaire
            if timeframe == '4h':
                df = df.resample('4h').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
            
            # Calculer les MA
            ma_values = {}
            for period in ma_system:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
                ma_values[period] = df[f'MA{period}'].iloc[-1]
            
            current_price = df['close'].iloc[-1]
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_price': current_price,
                'ma_values': ma_values,
                'df': df,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Erreur stock MA {symbol}: {e}")
            return None
    
    def detect_cross(self, data: Dict, ma_fast: int, ma_slow: int) -> Optional[str]:
        """Détecte un croisement entre deux MA"""
        try:
            df = data['df']
            
            ma_fast_current = df[f'MA{ma_fast}'].iloc[-1]
            ma_slow_current = df[f'MA{ma_slow}'].iloc[-1]
            ma_fast_prev = df[f'MA{ma_fast}'].iloc[-2]
            ma_slow_prev = df[f'MA{ma_slow}'].iloc[-2]
            
            if pd.isna(ma_fast_current) or pd.isna(ma_slow_current):
                return None
            if pd.isna(ma_fast_prev) or pd.isna(ma_slow_prev):
                return None
            
            # Golden Cross
            if ma_fast_prev <= ma_slow_prev and ma_fast_current > ma_slow_current:
                return 'golden_cross'
            
            # Death Cross
            if ma_fast_prev >= ma_slow_prev and ma_fast_current < ma_slow_current:
                return 'death_cross'
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur détection croisement: {e}")
            return None
    
    def check_alignment(self, data: Dict, ma_system: List[int]) -> Optional[str]:
        """Vérifie l'alignement des MA"""
        ma_values = data['ma_values']
        
        if not all(period in ma_values for period in ma_system):
            return None
        
        sorted_by_value = sorted([(p, ma_values[p]) for p in ma_system], key=lambda x: x[1], reverse=True)
        current_order = [p for p, _ in sorted_by_value]
        
        # Alignement haussier
        expected_bullish = sorted(ma_system)
        if current_order == expected_bullish:
            return 'bullish_alignment'
        
        # Alignement baissier
        expected_bearish = sorted(ma_system, reverse=True)
        if current_order == expected_bearish:
            return 'bearish_alignment'
        
        return None
    
    def check_compression(self, data: Dict, ma_system: List[int]) -> Optional[float]:
        """Vérifie la compression des MA"""
        ma_values = data['ma_values']
        
        if not all(period in ma_values for period in ma_system):
            return None
        
        ma_vals = [ma_values[p] for p in ma_system]
        max_ma = max(ma_vals)
        min_ma = min(ma_vals)
        
        if min_ma == 0:
            return None
        
        compression_pct = ((max_ma - min_ma) / min_ma) * 100
        
        return compression_pct
    
    def send_discord_alert(self, alert_type: str, data: Dict, details: Dict):
        """Envoie une alerte Discord - FORMAT CLAIR avec routing par webhook"""
        
        # Router vers le bon webhook selon le type d'alerte
        webhook_map = {
            'golden_cross': 'cross',
            'death_cross': 'cross',
            'bullish_cross': 'cross',
            'bearish_cross': 'cross',
            'bullish_alignment': 'alignment',
            'bearish_alignment': 'alignment',
            'compression': 'compression'
        }
        
        webhook_key = webhook_map.get(alert_type)
        if not webhook_key:
            print(f"⚠️  Type d'alerte inconnu: {alert_type}")
            return
        
        # Récupérer l'URL du webhook
        webhooks = self.config.get('webhooks', {})
        webhook_url = webhooks.get(webhook_key)
        
        if not webhook_url:
            print(f"⚠️  Webhook non configuré pour: {webhook_key}")
            return
        
        alert_configs = {
            'golden_cross': {
                'emoji': '🟢',
                'title': 'GOLDEN CROSS',
                'color': 0x00FF00,
            },
            'death_cross': {
                'emoji': '🔴',
                'title': 'DEATH CROSS',
                'color': 0xFF0000,
            },
            'bullish_cross': {
                'emoji': '🔼',
                'title': 'CROISEMENT HAUSSIER',
                'color': 0x90EE90,  # Vert clair
            },
            'bearish_cross': {
                'emoji': '🔽',
                'title': 'CROISEMENT BAISSIER',
                'color': 0xFFB6C1,  # Rouge clair
            },
            'bullish_alignment': {
                'emoji': '🟢',
                'title': 'ALIGNEMENT HAUSSIER COMPLET',
                'color': 0x00FF00,
            },
            'bearish_alignment': {
                'emoji': '🔴',
                'title': 'ALIGNEMENT BAISSIER COMPLET',
                'color': 0xFF0000,
            },
            'compression': {
                'emoji': '🔥',
                'title': 'COMPRESSION MA',
                'color': 0xFFA500,
            }
        }
        
        config = alert_configs.get(alert_type)
        if not config:
            return
        
        symbol_display = data['symbol'].replace('USDT', '').replace('BUSD', '')
        
        # Construction des champs
        fields = [
            {
                "name": "━━━━━━━━━━━━━━━━━━━━━━",
                "value": "** **",
                "inline": False
            },
            {
                "name": "📊 SITUATION",
                "value": (
                    f"**Symbole:** {symbol_display}\n"
                    f"**Prix actuel:** ${data['current_price']:,.2f}\n"
                    f"**Timeframe:** {data['timeframe'].upper()}\n"
                    f"**Heure:** {data['timestamp'].strftime('%H:%M:%S')}"
                ),
                "inline": False
            },
            {
                "name": "━━━━━━━━━━━━━━━━━━━━━━",
                "value": "** **",
                "inline": False
            }
        ]
        
        # Détails selon le type d'alerte
        if alert_type in ['golden_cross', 'death_cross']:
            ma_fast = details['ma_fast']
            ma_slow = details['ma_slow']
            direction = "à la hausse 📈" if alert_type == 'golden_cross' else "à la baisse 📉"
            
            fields.append({
                "name": "🔄 CROISEMENT DÉTECTÉ",
                "value": f"**MA{ma_fast}** croise **MA{ma_slow}** {direction}",
                "inline": False
            })
        
        elif alert_type == 'compression':
            compression = details['compression']
            fields.append({
                "name": "📊 COMPRESSION",
                "value": f"Écart entre toutes les MA: **{compression:.2f}%**\n└ Seuil: < {self.config['compression_threshold']}%",
                "inline": False
            })
        
        # Ajouter les MA
        ma_text = ""
        for period, value in sorted(data['ma_values'].items()):
            if pd.notna(value):
                ma_text += f"MA{period}: `${value:>10,.2f}`\n"
        
        if ma_text:
            fields.append({
                "name": "━━━━━━━━━━━━━━━━━━━━━━",
                "value": "** **",
                "inline": False
            })
            fields.append({
                "name": "📈 MOYENNES MOBILES",
                "value": ma_text,
                "inline": False
            })
        
        embed = {
            "title": f"{config['emoji']} {config['title']} - {symbol_display}",
            "color": config['color'],
            "fields": fields,
            "footer": {
                "text": f"{data['timeframe'].upper()} • {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
            },
            "timestamp": data['timestamp'].isoformat()
        }
        
        payload = {"embeds": [embed]}
        
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code == 204:
                print(f"✅ Alerte MA envoyée: {alert_type} → {webhook_key} - {data['symbol']}")
            else:
                print(f"❌ Erreur webhook: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur envoi: {e}")
    
    def check_all_assets(self, silent_mode: bool = False) -> List[Dict]:
        """
        Vérifie tous les actifs et envoie des alertes si nécessaire
        
        Args:
            silent_mode: Si True, ne pas envoyer d'alertes (mode warm-up)
        """
        alerts_sent = []
        
        for timeframe in self.config['timeframes']:
            # Cryptos - Système 1
            for crypto in self.config['assets']['crypto']:
                data1 = self.get_crypto_ma_data(crypto, timeframe, self.ma_system1)
                if data1:
                    alerts = self._check_asset_alerts(data1, self.ma_system1, 'system1', silent_mode)
                    alerts_sent.extend(alerts)
                
                # Système 2
                data2 = self.get_crypto_ma_data(crypto, timeframe, self.ma_system2)
                if data2:
                    alerts = self._check_asset_alerts(data2, self.ma_system2, 'system2', silent_mode)
                    alerts_sent.extend(alerts)
            
            # Stocks - Système 1
            for stock in self.config['assets']['stocks']:
                data1 = self.get_stock_ma_data(stock, timeframe, self.ma_system1)
                if data1:
                    alerts = self._check_asset_alerts(data1, self.ma_system1, 'system1', silent_mode)
                    alerts_sent.extend(alerts)
                
                # Système 2
                data2 = self.get_stock_ma_data(stock, timeframe, self.ma_system2)
                if data2:
                    alerts = self._check_asset_alerts(data2, self.ma_system2, 'system2', silent_mode)
                    alerts_sent.extend(alerts)
        
        return alerts_sent

    def _check_asset_alerts(self, data: Dict, ma_system: List[int], system_name: str, silent_mode: bool = False) -> List[Dict]:
        """
        Vérifie les alertes pour un actif
        
        Args:
            silent_mode: Si True, marquer les alertes SANS les envoyer
        """
        alerts = []
        
        # 1. Croisements (tous + distinction Golden/Death Cross)
        if self.config['alert_types']['golden_cross'] or self.config['alert_types']['death_cross']:
            for i in range(len(ma_system) - 1):
                ma_fast = ma_system[i]
                ma_slow = ma_system[i + 1]
                
                cross_type = self.detect_cross(data, ma_fast, ma_slow)
                
                if cross_type:
                    # Déterminer si c'est un Golden/Death Cross (MA50×MA200) ou un simple croisement
                    is_golden_death = (ma_fast == 50 and ma_slow == 200)
                    
                    if is_golden_death:
                        # Golden Cross ou Death Cross
                        alert_type = 'golden_cross' if cross_type == 'golden_cross' else 'death_cross'
                    else:
                        # Croisement simple
                        alert_type = 'bullish_cross' if cross_type == 'golden_cross' else 'bearish_cross'
                    
                    alert_key = f"{data['symbol']}_{data['timeframe']}_{system_name}_{ma_fast}_{ma_slow}_{alert_type}"
                    
                    if self._can_send_alert(alert_key):
                        if not silent_mode:
                            self.send_discord_alert(alert_type, data, {
                                'ma_fast': ma_fast,
                                'ma_slow': ma_slow
                            })
                        self._mark_alert_sent(alert_key)
                        alerts.append({
                            'symbol': data['symbol'],
                            'type': alert_type,
                            'system': system_name
                        })
        
        # 2. Alignement
        if self.config['alert_types']['alignment']:
            alignment = self.check_alignment(data, ma_system)
            
            if alignment:
                alert_key = f"{data['symbol']}_{data['timeframe']}_{system_name}_{alignment}"
                
                if self._can_send_alert(alert_key):
                    if not silent_mode:
                        self.send_discord_alert(alignment, data, {})
                    self._mark_alert_sent(alert_key)
                    alerts.append({
                        'symbol': data['symbol'],
                        'type': alignment,
                        'system': system_name
                    })
        
        # 3. Compression
        if self.config['alert_types']['compression']:
            compression = self.check_compression(data, ma_system)
            
            if compression and compression < self.config['compression_threshold']:
                alert_key = f"{data['symbol']}_{data['timeframe']}_{system_name}_compression"
                
                if self._can_send_alert(alert_key):
                    if not silent_mode:
                        self.send_discord_alert('compression', data, {
                            'compression': compression
                        })
                    self._mark_alert_sent(alert_key)
                    alerts.append({
                        'symbol': data['symbol'],
                        'type': 'compression',
                        'compression': compression,
                        'system': system_name
                    })
        
        return alerts
    
    def sync_assets_from_managers(self, crypto_symbols: List[str], stock_symbols: List[str]):
        """
        Synchronise les actifs surveillés avec les managers crypto/stock
        
        Args:
            crypto_symbols: Liste des symboles Binance (ex: ['BTCUSDT', 'ETHUSDT'])
            stock_symbols: Liste des symboles stocks (ex: ['AAPL', 'MSFT'])
        """
        self.config['assets']['crypto'] = crypto_symbols
        self.config['assets']['stocks'] = stock_symbols
        self._save_config()
        print(f"✅ MA Alerts: Actifs synchronisés - {len(crypto_symbols)} cryptos, {len(stock_symbols)} stocks")