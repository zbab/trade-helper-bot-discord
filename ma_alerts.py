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
        self.ma_system1 = [7, 13, 20, 25, 32, 50, 100, 200, 300]  # Court terme (ajout MA7 et MA20)
        self.ma_system2 = [112, 336, 375, 448, 750]    # Long terme

        # Paires de MA spécifiques à surveiller pour croisements
        self.ma_pairs_to_watch = [
            (7, 20),    # Très court terme
            (20, 50),   # Court terme
            (13, 25),   # Paire 1
            (25, 32),   # Paire 2
            (32, 100),  # Paire 3
            (100, 200), # Paire 4 (Golden/Death Cross)
        ]

        # Croisements MA112 avec long terme
        self.ma_112_crosses = [
            (112, 336),
            (112, 375),
            (112, 448),
            (112, 750),
        ]

        # Système de priorités des signaux (basé sur analyse technique)
        # Tier 1 (10/10) : Signaux institutionnels majeurs
        # Tier 2 (8-9/10) : Signaux majeurs
        # Tier 3 (6-7/10) : Signaux bons
        # Tier 4 (4-5/10) : Signaux faibles
        self.signal_priorities = {
            # TIER 1 - Signaux institutionnels (10/10)
            (100, 200): {'tier': 1, 'rating': 10, 'name': 'Golden/Death Cross', 'win_rate': '72-80%'},
            'multi_112_long': {'tier': 1, 'rating': 10, 'name': 'Cycle Majeur MA112', 'win_rate': '85-90%'},

            # TIER 2 - Signaux majeurs (8-9/10)
            (20, 50): {'tier': 2, 'rating': 9, 'name': 'Swing Trading', 'win_rate': '68-72%'},
            (32, 100): {'tier': 2, 'rating': 8.5, 'name': 'Position Trading', 'win_rate': '70%'},
            'multi_13_mid': {'tier': 2, 'rating': 8, 'name': 'Confluence Court-Terme', 'win_rate': '68%'},

            # TIER 3 - Signaux bons (6-7/10) - Requires confirmation
            (25, 32): {'tier': 3, 'rating': 7, 'name': 'Day Trading', 'win_rate': '58-62%'},
            (13, 25): {'tier': 3, 'rating': 6.5, 'name': 'Scalping', 'win_rate': '54-58%'},
            (7, 20): {'tier': 3, 'rating': 6, 'name': 'Scalping Pro', 'win_rate': '50-55%'},
        }

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

    def get_signal_priority(self, ma_fast: int, ma_slow: int, is_multiple_cross: bool = False) -> Dict:
        """
        Récupère la priorité et le rating d'un signal

        Returns:
            dict: {'tier': int, 'rating': float, 'name': str, 'win_rate': str, 'emoji': str}
        """
        # Multi-cross MA112 (Tier 1)
        if is_multiple_cross and ma_fast == 112:
            priority = self.signal_priorities.get('multi_112_long', {})
            return {
                'tier': priority.get('tier', 1),
                'rating': priority.get('rating', 10),
                'name': priority.get('name', 'Cycle Majeur'),
                'win_rate': priority.get('win_rate', '85-90%'),
                'emoji': '🏆',  # Tier 1
                'stars': '⭐⭐⭐⭐⭐'
            }

        # Rechercher la paire exacte
        pair_key = (ma_fast, ma_slow)
        if pair_key in self.signal_priorities:
            priority = self.signal_priorities[pair_key]
            tier = priority.get('tier', 3)

            # Emoji selon le tier
            tier_emojis = {
                1: '🏆',  # Or - Tier 1
                2: '🥈',  # Argent - Tier 2
                3: '🥉'   # Bronze - Tier 3
            }

            # Étoiles selon le rating
            rating = priority.get('rating', 5)
            if rating >= 9:
                stars = '⭐⭐⭐⭐⭐'
            elif rating >= 8:
                stars = '⭐⭐⭐⭐'
            elif rating >= 6.5:
                stars = '⭐⭐⭐'
            else:
                stars = '⭐⭐'

            return {
                'tier': tier,
                'rating': rating,
                'name': priority.get('name', 'Signal MA'),
                'win_rate': priority.get('win_rate', 'N/A'),
                'emoji': tier_emojis.get(tier, '📊'),
                'stars': stars
            }

        # Signal non classifié (par défaut Tier 3)
        return {
            'tier': 3,
            'rating': 5,
            'name': 'Signal Standard',
            'win_rate': 'N/A',
            'emoji': '📊',
            'stars': '⭐⭐'
        }

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

    def _detect_multiple_crosses(self, data: Dict, ma_system: List[int]) -> Dict[int, List[int]]:
        """
        Détecte si une MA rapide croise plusieurs MA en même temps

        Returns:
            Dict {ma_fast: [list of MA crossed]}
            Ex: {13: [25, 32]} signifie que MA13 croise MA25 ET MA32
        """
        multiple_crosses = {}
        df = data['df']

        if len(df) < 2:
            return multiple_crosses

        # Pour chaque MA rapide du système
        for i, ma_fast in enumerate(ma_system[:-1]):  # Exclure la dernière
            crossed_mas = []

            # Vérifier croisement avec toutes les MA plus lentes
            for ma_slow in ma_system[i+1:]:
                cross_type = self.detect_cross(data, ma_fast, ma_slow)

                if cross_type:  # Si croisement détecté
                    crossed_mas.append(ma_slow)

            # Ne garder que si au moins 2 MA sont croisées
            if len(crossed_mas) >= 2:
                multiple_crosses[ma_fast] = crossed_mas

        return multiple_crosses
    
    def send_discord_alert(self, alert_type: str, data: Dict, details: Dict):
        """Envoie une alerte Discord - FORMAT CLAIR avec routing par webhook"""
        
        # Router vers le bon webhook selon le type d'alerte
        webhook_map = {
            'golden_cross': 'cross',
            'death_cross': 'cross',
            'bullish_cross': 'cross',
            'bearish_cross': 'cross',
            'multiple_cross': 'cross',  # Nouveau type
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
            },
            'multiple_cross': {
                'emoji': '⚡',
                'title': 'CROISEMENT MULTIPLE',
                'color': 0xFFD700,  # Or
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

            # Récupérer la priorité du signal
            priority_info = self.get_signal_priority(ma_fast, ma_slow)

            fields.append({
                "name": "🔄 CROISEMENT DÉTECTÉ",
                "value": (
                    f"**MA{ma_fast}** croise **MA{ma_slow}** {direction}\n\n"
                    f"{priority_info['emoji']} **{priority_info['name']}** {priority_info['stars']}\n"
                    f"└ Tier {priority_info['tier']} | Rating: {priority_info['rating']}/10\n"
                    f"└ Win Rate historique: {priority_info['win_rate']}"
                ),
                "inline": False
            })

        elif alert_type in ['bullish_cross', 'bearish_cross']:
            ma_fast = details['ma_fast']
            ma_slow = details['ma_slow']
            direction = "à la hausse 📈" if alert_type == 'bullish_cross' else "à la baisse 📉"

            # Récupérer la priorité du signal
            priority_info = self.get_signal_priority(ma_fast, ma_slow)

            fields.append({
                "name": "🔄 CROISEMENT DÉTECTÉ",
                "value": (
                    f"**MA{ma_fast}** croise **MA{ma_slow}** {direction}\n\n"
                    f"{priority_info['emoji']} **{priority_info['name']}** {priority_info['stars']}\n"
                    f"└ Tier {priority_info['tier']} | Rating: {priority_info['rating']}/10\n"
                    f"└ Win Rate historique: {priority_info['win_rate']}"
                ),
                "inline": False
            })
            
        elif alert_type == 'compression':
            compression = details['compression']
            fields.append({
                "name": "📊 COMPRESSION",
                "value": f"Écart entre toutes les MA: **{compression:.2f}%**\n└ Seuil: < {self.config['compression_threshold']}%",
                "inline": False
            })

        elif alert_type == 'multiple_cross':
            ma_fast = details['ma_fast']
            crossed_mas = details['crossed_mas']
            crossed_list = ", ".join([f"MA{ma}" for ma in crossed_mas])

            # Vérifier si c'est un multi-cross MA112 (Tier 1)
            is_ma112_multi = (ma_fast == 112 and len(crossed_mas) >= 3)
            priority_info = self.get_signal_priority(ma_fast, 0, is_multiple_cross=is_ma112_multi)

            value_text = f"**MA{ma_fast}** croise simultanément **{len(crossed_mas)} moyennes** :\n└ {crossed_list}"

            # Ajouter info de priorité si c'est un signal important
            if is_ma112_multi:
                value_text += f"\n\n{priority_info['emoji']} **{priority_info['name']}** {priority_info['stars']}\n"
                value_text += f"└ Tier {priority_info['tier']} | Rating: {priority_info['rating']}/10\n"
                value_text += f"└ Win Rate historique: {priority_info['win_rate']}\n"
                value_text += "└ ⚠️ **SIGNAL EXTRÊMEMENT RARE - OPPORTUNITÉ GÉNÉRATIONNELLE**"

            fields.append({
                "name": "⚡ CROISEMENT MULTIPLE DÉTECTÉ",
                "value": value_text,
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

        # 1. Croisements de paires spécifiques
        if self.config['alert_types']['golden_cross'] or self.config['alert_types']['death_cross']:
            # A) Paires spécifiques du système 1 (7-20, 20-50, 13-25, 25-32, 32-100, 100-200)
            if system_name == 'system1':
                for ma_fast, ma_slow in self.ma_pairs_to_watch:
                    # Vérifier que les deux MA existent dans le système actuel
                    if ma_fast not in ma_system or ma_slow not in ma_system:
                        continue

                    cross_type = self.detect_cross(data, ma_fast, ma_slow)

                    if cross_type:
                        # Golden/Death Cross pour MA50×MA200
                        is_golden_death = (ma_fast == 50 and ma_slow == 200)

                        if is_golden_death:
                            alert_type = 'golden_cross' if cross_type == 'golden_cross' else 'death_cross'
                        else:
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
                                'system': system_name,
                                'ma_fast': ma_fast,
                                'ma_slow': ma_slow
                            })

            # B) Croisements MA112 avec long terme (système 2)
            if system_name == 'system2':
                for ma_fast, ma_slow in self.ma_112_crosses:
                    if ma_fast not in ma_system or ma_slow not in ma_system:
                        continue

                    cross_type = self.detect_cross(data, ma_fast, ma_slow)

                    if cross_type:
                        alert_type = 'bullish_cross' if cross_type == 'golden_cross' else 'bearish_cross'
                        alert_key = f"{data['symbol']}_{data['timeframe']}_{system_name}_MA112_{ma_slow}_{alert_type}"

                        if self._can_send_alert(alert_key):
                            if not silent_mode:
                                self.send_discord_alert(alert_type, data, {
                                    'ma_fast': ma_fast,
                                    'ma_slow': ma_slow
                                })
                            self._mark_alert_sent(alert_key)
                            alerts.append({
                                'symbol': data['symbol'],
                                'type': f'ma112_cross_{ma_slow}',
                                'system': system_name,
                                'ma_fast': ma_fast,
                                'ma_slow': ma_slow
                            })

            # C) Détection de croisements multiples (MA basse croise 2+ MA en même temps)
            # Uniquement système 1
            if system_name == 'system1':
                multiple_crosses = self._detect_multiple_crosses(data, ma_system)

                for ma_fast, crossed_mas in multiple_crosses.items():
                    if len(crossed_mas) >= 2:  # Minimum 2 MA croisées
                        alert_key = f"{data['symbol']}_{data['timeframe']}_{system_name}_multiple_MA{ma_fast}"

                        if self._can_send_alert(alert_key):
                            if not silent_mode:
                                self.send_discord_alert('multiple_cross', data, {
                                    'ma_fast': ma_fast,
                                    'crossed_mas': crossed_mas
                                })
                            self._mark_alert_sent(alert_key)
                            alerts.append({
                                'symbol': data['symbol'],
                                'type': 'multiple_cross',
                                'system': system_name,
                                'ma_fast': ma_fast,
                                'crossed_count': len(crossed_mas)
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