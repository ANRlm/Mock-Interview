import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

logger = logging.getLogger(__name__)


class TestSenseVoiceSTTException:
    @pytest.mark.asyncio
    async def test_health_check_failure_is_logged(self):
        base_url = "http://localhost:8080"

        with patch("app.services.sensevoice_stt_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Connection refused")

            with patch("app.services.sensevoice_stt_service.logger") as mock_logger:
                from app.services.sensevoice_stt_service import SenseVoiceSTTService
                stt = SenseVoiceSTTService()
                stt._base_url = base_url
                stt._timeout = 5.0
                result = await stt.ensure_model_ready()

            assert mock_logger.warning.called, "logger.warning should be called when health check fails"
            call_args_list = mock_logger.warning.call_args_list
            assert len(call_args_list) >= 1, "At least one warning should be logged"

            first_warning_call = call_args_list[0]
            assert "SenseVoice health check failed" in str(first_warning_call)
            assert base_url in str(first_warning_call)

    @pytest.mark.asyncio
    async def test_docs_endpoint_check_failure_is_logged(self):
        base_url = "http://localhost:8080"

        with patch("app.services.sensevoice_stt_service.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.side_effect = [
                Exception("Connection refused"),
                Exception("Connection refused"),
            ]

            with patch("app.services.sensevoice_stt_service.logger") as mock_logger:
                from app.services.sensevoice_stt_service import SenseVoiceSTTService
                stt = SenseVoiceSTTService()
                stt._base_url = base_url
                stt._timeout = 5.0
                result = await stt.ensure_model_ready()

            assert mock_logger.warning.called, "logger.warning should be called when docs check fails"
