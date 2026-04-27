"""Tests for the new /transcribe REST endpoint and IDOR ownership helper."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException


class TestAssertSessionOwner:
    """Tests for _assert_session_owner helper added to interview.py."""

    def test_raises_404_when_session_is_none(self):
        from app.api.interview import _assert_session_owner

        user = MagicMock()
        user.id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            _assert_session_owner(None, user)
        assert exc_info.value.status_code == 404

    def test_raises_403_when_different_owner(self):
        from app.api.interview import _assert_session_owner

        session = MagicMock()
        session.user_id = uuid4()

        user = MagicMock()
        user.id = uuid4()  # different UUID

        with pytest.raises(HTTPException) as exc_info:
            _assert_session_owner(session, user)
        assert exc_info.value.status_code == 403

    def test_returns_session_when_owner_matches(self):
        from app.api.interview import _assert_session_owner

        uid = uuid4()
        session = MagicMock()
        session.user_id = uid

        user = MagicMock()
        user.id = uid

        result = _assert_session_owner(session, user)
        assert result is session


class TestResamplePcm:
    """Tests for the pure-Python PCM resampler (replaces audioop)."""

    def test_same_rate_returns_unchanged_bytes(self):
        from app.services.audio_utils import resample_pcm_s16le

        data = b"\x00\x01" * 100
        result = resample_pcm_s16le(data, 16000, 16000)
        assert result == data

    def test_downsamples_correctly(self):
        from app.services.audio_utils import resample_pcm_s16le

        # 1 second at 32 kHz, silence
        pcm_32k = b"\x00\x00" * 32000
        result = resample_pcm_s16le(pcm_32k, 32000, 16000)
        # Result should be approximately half the number of samples
        assert len(result) // 2 == pytest.approx(16000, rel=0.01)

    def test_empty_input_returns_empty(self):
        from app.services.audio_utils import resample_pcm_s16le

        result = resample_pcm_s16le(b"", 16000, 8000)
        assert result == b""

    def test_upsample_doubles_samples(self):
        from app.services.audio_utils import resample_pcm_s16le

        import struct
        # 100 samples at 8 kHz
        pcm = struct.pack("<" + "h" * 100, *range(100))
        result = resample_pcm_s16le(pcm, 8000, 16000)
        # Should produce approximately 200 samples
        assert len(result) // 2 == pytest.approx(200, rel=0.01)

    def test_output_is_valid_s16le(self):
        from app.services.audio_utils import resample_pcm_s16le

        import struct
        pcm = struct.pack("<" + "h" * 64, *range(64))
        result = resample_pcm_s16le(pcm, 16000, 8000)
        # Must have even number of bytes
        assert len(result) % 2 == 0
        # Must parse without error as signed 16-bit ints
        samples = struct.unpack("<" + "h" * (len(result) // 2), result)
        assert all(-32768 <= s <= 32767 for s in samples)
