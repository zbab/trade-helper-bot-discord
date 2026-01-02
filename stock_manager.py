import json
import os
from typing import List, Dict, Optional

class StockManager:
    """Gestionnaire de la liste des actions/indices supportés"""
    
    def __init__(self, filename: str = "stocks.json"):
        self.filename = filename
        self.stocks = self._load_stocks()
    
    def _load_stocks(self) -> Dict[str, str]:
        """Charge la liste des stocks depuis le fichier JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  Erreur lors de la lecture de {self.filename}, utilisation des valeurs par défaut")
                return self._get_default_stocks()
        else:
            # Créer le fichier avec les stocks par défaut
            default = self._get_default_stocks()
            self._save_stocks(default)
            return default
    
    def _get_default_stocks(self) -> Dict[str, str]:
        """Retourne la liste par défaut des stocks"""
        return {
            "AAPL": "AAPL",      # Apple
            "MSFT": "MSFT",      # Microsoft
            "SPX": "^GSPC",      # S&P 500
        }
    
    def _save_stocks(self, stocks: Dict[str, str] = None):
        """Sauvegarde la liste des stocks dans le fichier JSON"""
        if stocks is None:
            stocks = self.stocks
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(stocks, f, indent=2)
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def get_all_stocks(self) -> Dict[str, str]:
        """Retourne tous les stocks"""
        return self.stocks.copy()
    
    def get_stock_symbols(self) -> List[str]:
        """Retourne la liste des symboles (AAPL, MSFT, ...)"""
        return list(self.stocks.keys())
    
    def get_yfinance_symbol(self, symbol: str) -> Optional[str]:
        """Convertit un symbole en symbole yfinance"""
        symbol = symbol.upper()
        return self.stocks.get(symbol, None)
    
    def add_stock(self, symbol: str, yfinance_symbol: str) -> bool:
        """
        Ajoute un nouveau stock
        
        Args:
            symbol: Symbole court (ex: AAPL, SPX)
            yfinance_symbol: Symbole yfinance (ex: AAPL, ^GSPC)
            
        Returns:
            True si ajouté, False si déjà existant
        """
        symbol = symbol.upper()
        yfinance_symbol = yfinance_symbol.strip()
        
        if symbol in self.stocks:
            return False
        
        self.stocks[symbol] = yfinance_symbol
        self._save_stocks()
        return True
    
    def remove_stock(self, symbol: str) -> bool:
        """
        Supprime un stock
        
        Args:
            symbol: Symbole à supprimer
            
        Returns:
            True si supprimé, False si n'existe pas
        """
        symbol = symbol.upper()
        
        if symbol not in self.stocks:
            return False
        
        del self.stocks[symbol]
        self._save_stocks()
        return True
    
    def stock_exists(self, symbol: str) -> bool:
        """Vérifie si un stock existe"""
        return symbol.upper() in self.stocks
    
    def get_count(self) -> int:
        """Retourne le nombre de stocks"""
        return len(self.stocks)
    
    def validate_yfinance_symbol(self, yfinance_symbol: str) -> bool:
        """
        Valide qu'un symbole yfinance est au bon format
        Simple validation: ne doit pas être vide
        """
        if not yfinance_symbol or len(yfinance_symbol.strip()) == 0:
            return False
        return True
