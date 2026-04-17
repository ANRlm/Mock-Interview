import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

logger = logging.getLogger(__name__)


class TestTTSServiceCancelCandidates:
    @pytest.mark.asyncio
    async def test_cancel_candidates_re_raises_cancelled_error(self):
        text_len = 10

        async def mock_producer_that_cancels():
            await asyncio.sleep(0.01)
            raise asyncio.CancelledError("task cancelled")

        mock_task = asyncio.create_task(mock_producer_that_cancels())

        cancelled_error_raised = False
        with patch("app.services.tts_service.logger"):
            done, pending = await asyncio.wait([mock_task], timeout=0.1)
            for task in pending:
                task.cancel()
            for task in done:
                try:
                    await task
                except asyncio.CancelledError:
                    cancelled_error_raised = True
                except Exception as e:
                    logger.warning(
                        "Error awaiting cancelled TTS candidate text_len=%s: %s",
                        text_len,
                        repr(e),
                    )

        assert cancelled_error_raised, "CancelledError should be re-raised, not swallowed"

    @pytest.mark.asyncio
    async def test_cancel_candidates_logs_other_exceptions(self):
        text_len = 10

        async def mock_producer_that_fails():
            await asyncio.sleep(0.01)
            raise RuntimeError("producer error")

        mock_task = asyncio.create_task(mock_producer_that_fails())

        with patch("app.services.tts_service.logger") as mock_logger:
            done, pending = await asyncio.wait([mock_task], timeout=0.1)
            for task in pending:
                task.cancel()
            for task in done:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    mock_logger.warning(
                        "Error awaiting cancelled TTS candidate text_len=%s: %s",
                        text_len,
                        repr(e),
                    )

        assert mock_logger.warning.called, "logger.warning should be called for non-cancelled errors"
        call_args = mock_logger.warning.call_args
        assert "Error awaiting cancelled TTS candidate" in str(call_args)
        assert "producer error" in str(call_args)
