from binance.client import Client
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class BinanceMarketAnalyzer:
    """Analyseur de marché pour crypto via Binance"""
    
    def __init__(self):
        self.client = Client()  # Pas besoin de clé API pour données publiques
        self.ma_periods = [112, 336, 375, 448, 750]
        
    def get_historical_data(self, symbol: str, days: int = 1000) -> pd.DataFrame:
        """
        Récupère les données historiques depuis Binance
        
        Args:
            symbol: Symbole Binance (BTCUSDT, ETHUSDT)
            days: Nombre de jours d'historique
            
        Returns:
            DataFrame avec OHLCV + moyennes mobiles
        """
        try:
            # Calculer date de début
            start_date = (datetime.now() - timedelta(days=days)).strftime("%d %b, %Y")
            
            # Récupérer les klines
            klines = self.client.get_historical_klines(
                symbol,
                Client.KLINE_INTERVAL_1DAY,
                start_date
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
        
        # Ordre attendu pour alignement haussier: MA112 > MA336 > MA375 > MA448 > MA750
        # (prix au dessus des MA courtes, MA courtes au dessus des MA longues)
        current_order = [period for period, _ in ma_sorted_by_value]
        expected_bullish = self.ma_periods.copy()  # [112, 336, 375, 448, 750]
        expected_bearish = self.ma_periods.copy()
        expected_bearish.reverse()  # [750, 448, 375, 336, 112]
        
        is_bullish_aligned = current_order == expected_bullish
        is_bearish_aligned = current_order == expected_bearish
        
        # Calculer la compression (écart entre MA la plus haute et la plus basse)
        ma_vals = list(ma_values.values())
        max_ma = max(ma_vals)
        min_ma = min(ma_vals)
        compression_pct = ((max_ma - min_ma) / min_ma) * 100
        
        # Déterminer si c'est "compressé" (seuil: < 5%)
        is_compressed = compression_pct < 5.0
        
        current_price = latest['close']
        
        # Position du prix par rapport aux MA
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
        """
        Calcule les distances entre les MA consécutives
        
        Returns:
            Dict avec les distances entre MA
        """
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
    
    def analyze_symbol(self, symbol: str) -> Dict:
        """
        Analyse complète d'un symbole
        
        Args:
            symbol: Symbole Binance (BTCUSDT, ETHUSDT, etc.)
            
        Returns:
            Dict avec toute l'analyse
        """
        try:
            # Récupérer les données
            df = self.get_historical_data(symbol, days=1000)
            
            # Vérifier alignement
            alignment = self.check_ma_alignment(df)
            
            if alignment['status'] != 'success':
                return alignment
            
            # Calculer les distances
            distances = self.get_ma_distances(df)
            
            # Ajouter les distances à l'analyse
            alignment['ma_distances'] = distances
            alignment['symbol'] = symbol
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
        """
        Teste si un symbole existe sur Binance
        
        Args:
            binance_symbol: Symbole Binance à tester
            
        Returns:
            True si existe, False sinon
        """
        try:
            # Essayer de récupérer les dernières 24h
            ticker = self.client.get_ticker(symbol=binance_symbol)
            return ticker is not None
        except:
            return False
