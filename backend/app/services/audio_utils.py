"""Shared audio processing utilities.

Keeping these in a separate module:
- Avoids duplicating the resampler across stt_service and sensevoice_stt_service
- Makes unit-testing trivial (no heavy service dependencies)
- Python 3.13-safe: no audioop usage
"""
from __future__ import annotations

import array


def resample_pcm_s16le(pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
    """Resample mono 16-bit PCM between sample rates using linear interpolation.

    This is a drop-in replacement for the deprecated ``audioop.ratecv`` API which
    was removed in Python 3.13.  Quality is sufficient for speech-recognition
    purposes; for music use a higher-quality library (e.g. ``soxr``).

    Args:
        pcm:      Raw PCM bytes in signed-16-bit little-endian format.
        src_rate: Source sample rate in Hz.
        dst_rate: Target sample rate in Hz.

    Returns:
        Resampled PCM bytes in the same format.
    """
    if src_rate == dst_rate:
        return pcm

    n_src = len(pcm) // 2
    if n_src == 0:
        return pcm

    src_samples = array.array("h", pcm)
    ratio = src_rate / dst_rate
    n_dst = max(1, int(n_src / ratio))
    dst_samples = array.array("h", [0] * n_dst)

    for i in range(n_dst):
        src_pos = i * ratio
        idx = int(src_pos)
        frac = src_pos - idx
        s0 = src_samples[min(idx, n_src - 1)]
        s1 = src_samples[min(idx + 1, n_src - 1)]
        dst_samples[i] = int(s0 + frac * (s1 - s0))

    return dst_samples.tobytes()
