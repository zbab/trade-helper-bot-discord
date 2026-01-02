from binance.client import Client
import yfinance as yf
from typing import List, Dict, Optional

class BinanceSymbolSearch:
    """Recherche de symboles sur Binance"""
    
    def __init__(self):
        self.client = Client()
        self._all_symbols = None
        
    def get_all_symbols(self) -> List[Dict]:
        """Récupère tous les symboles Binance (avec cache)"""
        if self._all_symbols is None:
            try:
                exchange_info = self.client.get_exchange_info()
                self._all_symbols = [
                    {
                        'symbol': s['symbol'],
                        'baseAsset': s['baseAsset'],
                        'quoteAsset': s['quoteAsset'],
                        'status': s['status']
                    }
                    for s in exchange_info['symbols']
                    if s['status'] == 'TRADING'
                ]
            except Exception as e:
                print(f"Erreur lors de la récupération des symboles: {e}")
                self._all_symbols = []
        
        return self._all_symbols
    
    def search(self, query: str, quote_asset: str = 'USDT', limit: int = 10) -> List[Dict]:
        """
        Recherche des symboles Binance
        
        Args:
            query: Terme de recherche (ex: BTC, DOGE, SOL)
            quote_asset: Asset de cotation préféré (USDT par défaut)
            limit: Nombre max de résultats
            
        Returns:
            Liste de symboles correspondants
        """
        query = query.upper().strip()
        all_symbols = self.get_all_symbols()
        
        # Filtrer les symboles qui correspondent
        results = []
        exact_matches = []
        partial_matches = []
        
        for s in all_symbols:
            base = s['baseAsset']
            symbol = s['symbol']
            
            # Match exact sur baseAsset
            if base == query:
                if s['quoteAsset'] == quote_asset:
                    exact_matches.insert(0, s)  # Priorité à USDT
                else:
                    exact_matches.append(s)
            
            # Match partiel
            elif query in base or query in symbol:
                if s['quoteAsset'] == quote_asset:
                    partial_matches.insert(0, s)
                else:
                    partial_matches.append(s)
        
        # Combiner les résultats (exact d'abord, puis partiel)
        results = exact_matches + partial_matches
        
        # Limiter les résultats
        return results[:limit]
    
    def get_best_match(self, query: str) -> Optional[str]:
        """
        Trouve le meilleur match (USDT en priorité)
        
        Args:
            query: Symbole recherché (ex: BTC, SOL)
            
        Returns:
            Meilleur symbole Binance ou None
        """
        results = self.search(query, limit=1)
        
        if results:
            return results[0]['symbol']
        
        return None


class YFinanceSymbolSearch:
    """Recherche de symboles sur Yahoo Finance"""
    
    def __init__(self):
        # Mapping des symboles populaires
        self.popular_stocks = {
            # Tech
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corporation',
            'NFLX': 'Netflix Inc.',
            
            # Indices
            'SPX': '^GSPC (S&P 500)',
            'NDX': '^NDX (Nasdaq 100)',
            'DJI': '^DJI (Dow Jones)',
            'VIX': '^VIX (Volatility Index)',
            
            # Commodities
            'GOLD': 'GC=F (Gold Futures)',
            'SILVER': 'SI=F (Silver Futures)',
            'OIL': 'CL=F (Crude Oil)',
        }
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des symboles Yahoo Finance
        
        Args:
            query: Terme de recherche
            limit: Nombre max de résultats
            
        Returns:
            Liste de symboles correspondants
        """
        query = query.upper().strip()
        results = []
        
        # Recherche dans les populaires
        for symbol, name in self.popular_stocks.items():
            if query in symbol or query in name.upper():
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'yfinance_symbol': self._get_yfinance_symbol(symbol)
                })
        
        # Si pas de résultats dans les populaires, essayer directement
        if not results:
            # Tester si le symbole existe tel quel
            if self._test_symbol(query):
                results.append({
                    'symbol': query,
                    'name': 'Symbole trouvé',
                    'yfinance_symbol': query
                })
            
            # Tester avec des suffixes courants
            test_symbols = [
                query,
                f"^{query}",  # Indices
                f"{query}=F",  # Futures
            ]
            
            for test in test_symbols:
                if test != query and self._test_symbol(test):
                    results.append({
                        'symbol': query,
                        'name': f'Trouvé comme {test}',
                        'yfinance_symbol': test
                    })
        
        return results[:limit]
    
    def _get_yfinance_symbol(self, symbol: str) -> str:
        """Convertit un symbole en format yfinance"""
        # Mapping pour les symboles spéciaux
        special_map = {
            'SPX': '^GSPC',
            'NDX': '^NDX',
            'DJI': '^DJI',
            'VIX': '^VIX',
            'GOLD': 'GC=F',
            'SILVER': 'SI=F',
            'OIL': 'CL=F',
        }
        
        return special_map.get(symbol, symbol)
    
    def _test_symbol(self, symbol: str) -> bool:
        """Teste si un symbole existe sur yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d")
            return len(df) > 0
        except:
            return False
    
    def get_best_match(self, query: str) -> Optional[str]:
        """
        Trouve le meilleur match
        
        Args:
            query: Symbole recherché
            
        Returns:
            Meilleur symbole yfinance ou None
        """
        query = query.upper().strip()
        
        # Vérifier d'abord dans les populaires
        if query in self.popular_stocks:
            return self._get_yfinance_symbol(query)
        
        # Sinon chercher
        results = self.search(query, limit=1)
        
        if results:
            return results[0]['yfinance_symbol']
        
        # Dernier essai : tester le symbole tel quel
        if self._test_symbol(query):
            return query
        
        return None
