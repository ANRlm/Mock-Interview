import struct
from typing import NamedTuple


class EchoCancellationResult(NamedTuple):
    output: bytes
    echo_reduced_db: float


class EchoCanceller:
    def __init__(self):
        self._enabled = True
        self._tail_length = 256
        self._scale = 0.3

    def process(self, mic_audio: bytes, speaker_audio: bytes) -> EchoCancellationResult:
        """Simple energy-based echo reduction."""
        if not self._enabled or len(mic_audio) == 0:
            return EchoCancellationResult(output=mic_audio, echo_reduced_db=0.0)

        # Calculate speaker energy
        speaker_samples = len(speaker_audio) // 2
        if speaker_samples == 0:
            return EchoCancellationResult(output=mic_audio, echo_reduced_db=0.0)

        speaker_values = struct.unpack(f'<{speaker_samples}h', speaker_audio)
        speaker_energy = sum(abs(v) for v in speaker_values) / speaker_samples

        # Subtract scaled speaker signal from mic
        mic_samples = len(mic_audio) // 2
        mic_values = list(struct.unpack(f'<{mic_samples}h', mic_audio))

        for i in range(min(mic_samples, speaker_samples)):
            mic_values[i] = int(mic_values[i] - speaker_values[i] * self._scale)

        output = struct.pack(f'<{mic_samples}h', *mic_values)
        echo_reduced = 20  # Simplified calculation
        return EchoCancellationResult(output=output, echo_reduced_db=echo_reduced)

    def enable(self) -> None:
        """Enable echo cancellation."""
        self._enabled = True

    def disable(self) -> None:
        """Disable echo cancellation."""
        self._enabled = False

    @property
    def enabled(self) -> bool:
        """Check if echo cancellation is enabled."""
        return self._enabled


echo_canceller = EchoCanceller()