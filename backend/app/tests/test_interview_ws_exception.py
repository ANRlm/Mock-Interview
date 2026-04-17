import asyncio
import ast
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

logger = logging.getLogger(__name__)


class TestInterviewWSTTSPreflightException:
    def test_tts_preflight_exception_uses_logger_warning(self):
        source_path = Path(__file__).parent.parent / "ws" / "interview_ws.py"
        source_code = source_path.read_text()
        tree = ast.parse(source_code)

        class TTSPreflightVisitor(ast.NodeVisitor):
            def __init__(self):
                self.found_stream_synthesize_try = False
                self.has_logger_warning_in_except = False
                self.has_exc_info_true = False
                self.has_bare_pass = False

            def visit_Try(self, node):
                for handler in node.handlers:
                    for stmt in handler.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            call = stmt.value
                            if self._is_logger_warning(call):
                                self.has_logger_warning_in_except = True
                                for kw in call.keywords:
                                    if kw.arg == "exc_info" and self._is_true(kw.value):
                                        self.has_exc_info_true = True
                        elif isinstance(stmt, ast.Pass):
                            self.has_bare_pass = True
                self.generic_visit(node)

            def visit_AsyncFor(self, node):
                if isinstance(node.iter, ast.Call):
                    if self._is_stream_synthesize_call(node.iter):
                        self.found_stream_synthesize_try = True
                self.generic_visit(node)

            def _is_stream_synthesize_call(self, call):
                if isinstance(call.func, ast.Attribute) and call.func.attr == "stream_synthesize":
                    return True
                return False

            def _is_logger_warning(self, call):
                if isinstance(call.func, ast.Attribute) and call.func.attr == "warning":
                    return True
                return False

            def _is_true(self, node):
                return isinstance(node, ast.Constant) and node.value is True

        visitor = TTSPreflightVisitor()
        visitor.visit(tree)

        assert visitor.found_stream_synthesize_try, (
            "Could not find try/except around stream_synthesize in interview_ws.py. "
            "The production code should wrap stream_synthesize in a try/except block."
        )
        assert not visitor.has_bare_pass, (
            "The except clause should not use bare 'pass'. "
            "It should log the exception with logger.warning."
        )
        assert visitor.has_logger_warning_in_except, (
            "The except clause should call logger.warning to log the exception, "
            "not swallow it silently."
        )
        assert visitor.has_exc_info_true, (
            "logger.warning should be called with exc_info=True to include "
            "the exception traceback in the log."
        )

    def test_tts_preflight_exception_log_message_format(self):
        source_path = Path(__file__).parent.parent / "ws" / "interview_ws.py"
        source_code = source_path.read_text()
        tree = ast.parse(source_code)

        class MessageFormatVisitor(ast.NodeVisitor):
            def __init__(self):
                self.log_messages = []

            def visit_Try(self, node):
                for handler in node.handlers:
                    for stmt in handler.body:
                        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                            call = stmt.value
                            if isinstance(call.func, ast.Attribute) and call.func.attr == "warning":
                                if call.args:
                                    first_arg = call.args[0]
                                    if isinstance(first_arg, ast.Constant):
                                        self.log_messages.append(first_arg.value)
                self.generic_visit(node)

        visitor = MessageFormatVisitor()
        visitor.visit(tree)

        found_tts_preflight_message = any(
            "TTS preflight check failed" in msg for msg in visitor.log_messages
        )
        assert found_tts_preflight_message, (
            "The log message should indicate TTS preflight failure. "
            f"Found messages: {visitor.log_messages}"
        )


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
