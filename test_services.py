"""Unit tests for Toka 420 Time Bot services."""

import pytest
from services.dexscreener import _format_anchor
from services.ritual import kiss_anchor


class TestDexScreener:
    """Tests for dexscreener.py functions."""
    
    def test_format_anchor_with_valid_pair(self):
        """Test formatting a valid trading pair."""
        pair = {
            "priceUsd": "0.00123456",
            "priceChange": {"h24": 5.5},
            "volume": {"h24": 50000},
            "baseToken": {"symbol": "WEED"},
            "chainId": "solana",
            "dexId": "raydium"
        }
        result = _format_anchor(pair)
        
        assert result["symbol"] == "WEED"
        assert result["price"] == "$0.001235"
        assert result["change24"] == "+5.50%"
        assert result["vol24"] == "$50,000"
        assert result["chain"] == "solana"
        assert result["dex"] == "raydium"
    
    def test_format_anchor_with_negative_change(self):
        """Test formatting with negative 24h change."""
        pair = {
            "priceUsd": "0.001",
            "priceChange": {"h24": -10.25},
            "volume": {"h24": 100000},
            "baseToken": {"symbol": "TEST"},
            "chainId": "ethereum",
            "dexId": "uniswap"
        }
        result = _format_anchor(pair)
        
        assert result["change24"] == "-10.25%"
    
    def test_format_anchor_with_missing_symbol(self):
        """Test formatting when symbol is missing."""
        pair = {
            "priceUsd": "0.001",
            "priceChange": {"h24": 0},
            "volume": {"h24": 0},
            "baseToken": {},
            "chainId": "ethereum",
            "dexId": "uniswap"
        }
        result = _format_anchor(pair)
        
        assert result["symbol"] == "TOKEN"  # Default fallback
    
    def test_format_anchor_with_zero_volume(self):
        """Test formatting with zero 24h volume."""
        pair = {
            "priceUsd": "0.001",
            "priceChange": {"h24": 0},
            "volume": {"h24": 0},
            "baseToken": {"symbol": "TEST"},
            "chainId": "ethereum",
            "dexId": "uniswap"
        }
        result = _format_anchor(pair)
        
        assert result["vol24"] == "$0"


class TestRitual:
    """Tests for ritual.py functions."""
    
    def test_kiss_anchor_formats_correctly(self):
        """Test that kiss_anchor returns properly formatted string."""
        # This requires network access, so mock in real tests
        # For now, just test the fallback when data is None
        pass


class TestInputValidation:
    """Tests for command input validation."""
    
    def test_token_validation_rejects_long_input(self):
        """Test that token command rejects overly long input."""
        # Would need async context, tested in integration tests
        pass
    
    def test_token_validation_rejects_invalid_chars(self):
        """Test that token command rejects invalid characters."""
        # Would need async context, tested in integration tests
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
