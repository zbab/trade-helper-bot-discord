from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import yfinance as yf

class BinanceMarketAnalyzer:
    """Analyseur de marché pour crypto via Binance"""
    
    def __init__(self):
        self.client = Client()
        self.ma_periods = [112, 336, 375, 448, 750]
        
        # Mapping des intervals utilisateur vers Binance
        self.interval_map = {
            '5m': Client.KLINE_INTERVAL_5MINUTE,
            '15m': Client.KLINE_INTERVAL_15MINUTE,
            '1h': Client.KLINE_INTERVAL_1HOUR,
            '4h': Client.KLINE_INTERVAL_4HOUR,
            '1d': Client.KLINE_INTERVAL_1DAY,
            'daily': Client.KLINE_INTERVAL_1DAY,
        }
        
        # Nombre de périodes à récupérer selon l'interval
        self.period_limits = {
            '5m': 1000,
            '15m': 1000,
            '1h': 1000,
            '4h': 1000,
            '1d': 1000,
            'daily': 1000,
        }
        
    def get_binance_interval(self, interval_str: str) -> str:
        """Convertit un interval utilisateur en interval Binance"""
        return self.interval_map.get(interval_str.lower(), Client.KLINE_INTERVAL_1DAY)
    
    def get_interval_label(self, interval_str: str) -> str:
        """Retourne un label lisible pour l'interval"""
        labels = {
            '5m': '5 Minutes',
            '15m': '15 Minutes',
            '1h': '1 Heure',
            '4h': '4 Heures',
            '1d': 'Daily',
            'daily': 'Daily',
        }
        return labels.get(interval_str.lower(), 'Daily')
        
    def get_historical_data(self, symbol: str, interval: str = '1d', limit: int = None) -> pd.DataFrame:
        """
        Récupère les données historiques depuis Binance
        
        Args:
            symbol: Symbole Binance (BTCUSDT, ETHUSDT)
            interval: Interval de temps ('5m', '15m', '1h', '4h', '1d')
            limit: Nombre de périodes à récupérer
            
        Returns:
            DataFrame avec OHLCV + moyennes mobiles
        """
        try:
            binance_interval = self.get_binance_interval(interval)
            
            if limit is None:
                limit = self.period_limits.get(interval.lower(), 1000)
            
            # Récupérer les klines
            klines = self.client.get_klines(
                symbol=symbol,
                interval=binance_interval,
                limit=limit
            )
            
            if not klines:
                raise ValueError(f"Aucune donnée pour {symbol}")
            
            # Convertir en DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convertir les types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            df.set_index('timestamp', inplace=True)
            
            # Calculer les moyennes mobiles
            for period in self.ma_periods:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
            return df
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des données: {e}")
    
    def check_ma_alignment(self, df: pd.DataFrame) -> Dict:
        """
        Vérifie l'alignement des moyennes mobiles
        
        Returns:
            Dict avec les informations d'alignement
        """
        latest = df.iloc[-1]
        
        # Récupérer les valeurs des MA
        ma_values = {}
        for period in self.ma_periods:
            ma_col = f'MA{period}'
            if ma_col in latest and pd.notna(latest[ma_col]):
                ma_values[period] = latest[ma_col]
        
        if len(ma_values) != len(self.ma_periods):
            return {
                'status': 'insufficient_data',
                'message': 'Pas assez de données pour calculer toutes les MA'
            }
        
        # Vérifier l'ordre des MA
        ma_list = [(period, value) for period, value in ma_values.items()]
        ma_sorted_by_value = sorted(ma_list, key=lambda x: x[1], reverse=True)
        
        current_order = [period for period, _ in ma_sorted_by_value]
        expected_bullish = self.ma_periods.copy()
        expected_bearish = self.ma_periods.copy()
        expected_bearish.reverse()
        
        is_bullish_aligned = current_order == expected_bullish
        is_bearish_aligned = current_order == expected_bearish
        
        # Calculer la compression
        ma_vals = list(ma_values.values())
        max_ma = max(ma_vals)
        min_ma = min(ma_vals)
        compression_pct = ((max_ma - min_ma) / min_ma) * 100
        
        is_compressed = compression_pct < 5.0
        
        current_price = latest['close']
        
        price_above_all = all(current_price > ma for ma in ma_vals)
        price_below_all = all(current_price < ma for ma in ma_vals)
        
        return {
            'status': 'success',
            'current_price': current_price,
            'ma_values': ma_values,
            'aligned_bullish': is_bullish_aligned,
            'aligned_bearish': is_bearish_aligned,
            'compression_pct': compression_pct,
            'is_compressed': is_compressed,
            'price_above_all_ma': price_above_all,
            'price_below_all_ma': price_below_all,
            'current_order': current_order,
            'timestamp': latest.name
        }
    
    def get_ma_distances(self, df: pd.DataFrame) -> Dict:
        """Calcule les distances entre les MA consécutives"""
        latest = df.iloc[-1]
        distances = {}
        
        for i in range(len(self.ma_periods) - 1):
            ma1 = self.ma_periods[i]
            ma2 = self.ma_periods[i + 1]
            
            ma1_val = latest[f'MA{ma1}']
            ma2_val = latest[f'MA{ma2}']
            
            if pd.notna(ma1_val) and pd.notna(ma2_val):
                distance_pct = abs((ma1_val - ma2_val) / ma2_val) * 100
                distances[f'MA{ma1}_MA{ma2}'] = distance_pct
        
        return distances
    
    def analyze_symbol(self, symbol: str, interval: str = '1d') -> Dict:
        """
        Analyse complète d'un symbole crypto
        
        Args:
            symbol: Symbole Binance
            interval: Timeframe ('5m', '15m', '1h', '4h', '1d')
        """
        try:
            df = self.get_historical_data(symbol, interval=interval)
            alignment = self.check_ma_alignment(df)
            
            if alignment['status'] != 'success':
                return alignment
            
            distances = self.get_ma_distances(df)
            
            alignment['ma_distances'] = distances
            alignment['symbol'] = symbol
            alignment['interval'] = interval
            alignment['interval_label'] = self.get_interval_label(interval)
            alignment['data_points'] = len(df)
            alignment['period_start'] = df.index[0]
            alignment['period_end'] = df.index[-1]
            
            return alignment
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'symbol': symbol
            }
    
    def test_symbol_exists(self, binance_symbol: str) -> bool:
        """Teste si un symbole existe sur Binance"""
        try:
            ticker = self.client.get_ticker(symbol=binance_symbol)
            return ticker is not None
        except:
            return False


class YFinanceMarketAnalyzer:
    """Analyseur de marché pour actions/indices via yfinance"""
    
    def __init__(self):
        self.ma_periods = [112, 336, 375, 448, 750]
        
        # Mapping des intervals pour yfinance (harmonisé avec Binance)
        self.interval_map = {
            '5m': '5m',
            '5min': '5m',
            '15m': '15m',
            '15min': '15m',
            '1h': '1h',
            'h1': '1h',
            '4h': '4h',
            'h4': '4h',
            '1d': '1d',
            'daily': '1d',
        }
    
    def get_yfinance_interval(self, interval_str: str) -> str:
        """Convertit un interval utilisateur en interval yfinance"""
        return self.interval_map.get(interval_str.lower(), '1d')
    
    def get_interval_label(self, interval_str: str) -> str:
        """Retourne un label lisible pour l'interval"""
        labels = {
            '5m': '5 Minutes',
            '5min': '5 Minutes',
            '15m': '15 Minutes',
            '15min': '15 Minutes',
            '1h': '1 Heure',
            'h1': '1 Heure',
            '4h': '4 Heures',
            'h4': '4 Heures',
            '1d': 'Daily',
            'daily': 'Daily',
        }
        return labels.get(interval_str.lower(), 'Daily')
    
    def get_period_for_interval(self, interval: str) -> str:
        """Retourne la période maximale disponible selon l'interval"""
        yf_interval = self.get_yfinance_interval(interval)
        
        # Yahoo Finance limitations
        period_map = {
            '5m': '60d',    # Max 60 jours pour 5min
            '15m': '60d',   # Max 60 jours pour 15min
            '1h': '730d',   # Max 730 jours pour 1h
            '4h': '730d',   # Max 730 jours pour 4h (pas natif, on utilise 1h et resample)
            '1d': 'max',    # Max pour daily
        }
        
        return period_map.get(yf_interval, 'max')
        
    def get_historical_data(self, symbol: str, interval: str = '1d') -> pd.DataFrame:
        """
        Récupère les données historiques depuis yfinance
        
        Args:
            symbol: Symbole yfinance (AAPL, ^GSPC, etc.)
            interval: Interval ('5m', '15m', '1h', '4h', '1d')
            
        Returns:
            DataFrame avec OHLCV + moyennes mobiles
        """
        try:
            # Créer le ticker
            ticker = yf.Ticker(symbol)
            
            yf_interval = self.get_yfinance_interval(interval)
            period = self.get_period_for_interval(interval)
            
            # Récupérer les données
            if yf_interval == '4h':
                # Yahoo ne supporte pas 4h natif, on récupère 1h et on resample
                df = ticker.history(period=period, interval='1h')
                if not df.empty:
                    # Renommer avant resample
                    df.columns = df.columns.str.lower()
                    # Resample en 4h
                    df = df.resample('4h').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
            else:
                df = ticker.history(period=period, interval=yf_interval)
                if not df.empty:
                    df.columns = df.columns.str.lower()
            
            if df.empty or len(df) == 0:
                raise ValueError(f"Aucune donnée pour {symbol}")
            
            # S'assurer que l'index est datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Calculer les moyennes mobiles
            for period in self.ma_periods:
                df[f'MA{period}'] = df['close'].rolling(window=period).mean()
            
            # Garder seulement les lignes où toutes les MA sont calculées
            df = df.dropna(subset=[f'MA{period}' for period in self.ma_periods])
            
            if len(df) == 0:
                raise ValueError(f"Pas assez de données historiques pour {symbol} sur {interval} (besoin de 750+ périodes)")
            
            return df
            
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des données: {e}")
    
    def check_ma_alignment(self, df: pd.DataFrame) -> Dict:
        """Vérifie l'alignement des moyennes mobiles"""
        latest = df.iloc[-1]
        
        ma_values = {}
        for period in self.ma_periods:
            ma_col = f'MA{period}'
            if ma_col in latest and pd.notna(latest[ma_col]):
                ma_values[period] = latest[ma_col]
        
        if len(ma_values) != len(self.ma_periods):
            return {
                'status': 'insufficient_data',
                'message': 'Pas assez de données pour calculer toutes les MA'
            }
        
        ma_list = [(period, value) for period, value in ma_values.items()]
        ma_sorted_by_value = sorted(ma_list, key=lambda x: x[1], reverse=True)
        
        current_order = [period for period, _ in ma_sorted_by_value]
        expected_bullish = self.ma_periods.copy()
        expected_bearish = self.ma_periods.copy()
        expected_bearish.reverse()
        
        is_bullish_aligned = current_order == expected_bullish
        is_bearish_aligned = current_order == expected_bearish
        
        ma_vals = list(ma_values.values())
        max_ma = max(ma_vals)
        min_ma = min(ma_vals)
        compression_pct = ((max_ma - min_ma) / min_ma) * 100
        
        is_compressed = compression_pct < 5.0
        
        current_price = latest['close']
        
        price_above_all = all(current_price > ma for ma in ma_vals)
        price_below_all = all(current_price < ma for ma in ma_vals)
        
        return {
            'status': 'success',
            'current_price': current_price,
            'ma_values': ma_values,
            'aligned_bullish': is_bullish_aligned,
            'aligned_bearish': is_bearish_aligned,
            'compression_pct': compression_pct,
            'is_compressed': is_compressed,
            'price_above_all_ma': price_above_all,
            'price_below_all_ma': price_below_all,
            'current_order': current_order,
            'timestamp': latest.name
        }
    
    def get_ma_distances(self, df: pd.DataFrame) -> Dict:
        """Calcule les distances entre les MA consécutives"""
        latest = df.iloc[-1]
        distances = {}
        
        for i in range(len(self.ma_periods) - 1):
            ma1 = self.ma_periods[i]
            ma2 = self.ma_periods[i + 1]
            
            ma1_val = latest[f'MA{ma1}']
            ma2_val = latest[f'MA{ma2}']
            
            if pd.notna(ma1_val) and pd.notna(ma2_val):
                distance_pct = abs((ma1_val - ma2_val) / ma2_val) * 100
                distances[f'MA{ma1}_MA{ma2}'] = distance_pct
        
        return distances
    
    def analyze_symbol(self, symbol: str, interval: str = '1d') -> Dict:
        """
        Analyse complète d'un symbole action/indice
        
        Args:
            symbol: Symbole yfinance
            interval: Timeframe ('5m', '15m', '1h', '4h', '1d')
        """
        try:
            df = self.get_historical_data(symbol, interval=interval)
            alignment = self.check_ma_alignment(df)
            
            if alignment['status'] != 'success':
                return alignment
            
            distances = self.get_ma_distances(df)
            
            alignment['ma_distances'] = distances
            alignment['symbol'] = symbol
            alignment['interval'] = interval
            alignment['interval_label'] = self.get_interval_label(interval)
            alignment['data_points'] = len(df)
            alignment['period_start'] = df.index[0]
            alignment['period_end'] = df.index[-1]
            
            return alignment
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'symbol': symbol
            }
    
    def test_symbol_exists(self, yfinance_symbol: str) -> bool:
        """Teste si un symbole existe sur yfinance"""
        try:
            ticker = yf.Ticker(yfinance_symbol)
            df = ticker.history(period="5d")
            return len(df) > 0
        except:
            return False
