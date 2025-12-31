import json
import os
from typing import List, Dict, Optional

class CryptoManager:
    """Gestionnaire de la liste des cryptos supportées"""
    
    def __init__(self, filename: str = "cryptos.json"):
        self.filename = filename
        self.cryptos = self._load_cryptos()
    
    def _load_cryptos(self) -> Dict[str, str]:
        """Charge la liste des cryptos depuis le fichier JSON"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️  Erreur lors de la lecture de {self.filename}, utilisation des valeurs par défaut")
                return self._get_default_cryptos()
        else:
            # Créer le fichier avec les cryptos par défaut
            default = self._get_default_cryptos()
            self._save_cryptos(default)
            return default
    
    def _get_default_cryptos(self) -> Dict[str, str]:
        """Retourne la liste par défaut des cryptos"""
        return {
            "BTC": "BTCUSDT",
            "ETH": "ETHUSDT"
        }
    
    def _save_cryptos(self, cryptos: Dict[str, str] = None):
        """Sauvegarde la liste des cryptos dans le fichier JSON"""
        if cryptos is None:
            cryptos = self.cryptos
        
        try:
            with open(self.filename, 'w') as f:
                json.dump(cryptos, f, indent=2)
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def get_all_cryptos(self) -> Dict[str, str]:
        """Retourne toutes les cryptos"""
        return self.cryptos.copy()
    
    def get_crypto_symbols(self) -> List[str]:
        """Retourne la liste des symboles (BTC, ETH, ...)"""
        return list(self.cryptos.keys())
    
    def get_binance_symbol(self, symbol: str) -> Optional[str]:
        """Convertit un symbole en symbole Binance"""
        symbol = symbol.upper()
        return self.cryptos.get(symbol, None)
    
    def add_crypto(self, symbol: str, binance_symbol: str) -> bool:
        """
        Ajoute une nouvelle crypto
        
        Args:
            symbol: Symbole court (ex: BTC, SOL)
            binance_symbol: Symbole Binance (ex: BTCUSDT, SOLUSDT)
            
        Returns:
            True si ajouté, False si déjà existant
        """
        symbol = symbol.upper()
        binance_symbol = binance_symbol.upper()
        
        if symbol in self.cryptos:
            return False
        
        self.cryptos[symbol] = binance_symbol
        self._save_cryptos()
        return True
    
    def remove_crypto(self, symbol: str) -> bool:
        """
        Supprime une crypto
        
        Args:
            symbol: Symbole à supprimer
            
        Returns:
            True si supprimé, False si n'existe pas
        """
        symbol = symbol.upper()
        
        if symbol not in self.cryptos:
            return False
        
        del self.cryptos[symbol]
        self._save_cryptos()
        return True
    
    def crypto_exists(self, symbol: str) -> bool:
        """Vérifie si une crypto existe"""
        return symbol.upper() in self.cryptos
    
    def get_count(self) -> int:
        """Retourne le nombre de cryptos"""
        return len(self.cryptos)
    
    def validate_binance_symbol(self, binance_symbol: str) -> bool:
        """
        Valide qu'un symbole Binance est au bon format
        Simple validation: doit se terminer par USDT, BUSD, ou BTC
        """
        binance_symbol = binance_symbol.upper()
        valid_endings = ['USDT', 'BUSD', 'BTC', 'ETH']
        return any(binance_symbol.endswith(ending) for ending in valid_endings)
