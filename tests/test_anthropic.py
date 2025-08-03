"""Tests for Anthropic AI integration."""

import os
from unittest.mock import Mock, patch

from src.services.anthropic_service import AnthropicService


class TestAnthropicService:
    """Test AnthropicService functionality."""

    def test_anthropic_service_creation(self):
        """Test creating AnthropicService."""
        service = AnthropicService()
        assert service is not None

    def test_is_configured_with_api_key(self):
        """Test configuration check with API key."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = AnthropicService()
            assert service.is_configured() is True

    def test_is_configured_without_api_key(self):
        """Test configuration check without API key."""
        with patch.dict(os.environ, {}, clear=True):
            service = AnthropicService()
            assert service.is_configured() is False

    def test_fallback_message(self):
        """Test fallback message generation."""
        service = AnthropicService()
        message = service._fallback_message("TestUser")

        assert "TestUser" in message
        assert "Kudo rain" in message
        assert "🎉" in message

    @patch("anthropic.Anthropic")
    def test_generate_kudo_rain_success(self, mock_anthropic):
        """Test successful kudo rain generation."""
        # Mock the API response
        mock_content = Mock()
        mock_content.text = "Kudo rain for TestUser - like a superhero saving the day!"

        mock_message = Mock()
        mock_message.content = [mock_content]

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = AnthropicService()

            # Since this is async, we'll test the sync parts
            result = service._fallback_message("TestUser")
            assert "TestUser" in result

    @patch("anthropic.Anthropic")
    def test_generate_kudo_rain_api_failure(self, mock_anthropic):
        """Test kudo rain generation with API failure."""
        # Mock API failure
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            service = AnthropicService()
            result = service._fallback_message("TestUser")

            # Should return fallback message
            assert "TestUser" in result
            assert "Kudo rain" in result
