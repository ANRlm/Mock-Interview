import { useCallback, useEffect, useRef, useState } from 'react'

import { isPotentiallyTrustworthyHost } from '@/hooks/useMediaPipe'

interface UseAudioRecorderParams {
  onChunk: (chunkBase64: string, sampleRate: number) => void
  onSpeechStart?: () => void
  onSpeechEnd: () => void
  enabled: boolean
}

interface UseAudioRecorderResult {
  isRecording: boolean
  micLevel: number
  start: () => Promise<void>
  stop: () => void
}

const CHUNK_MS = 120
const SILENCE_THRESHOLD = 0.016
const MAX_SILENCE_MS = 850
const TARGET_SAMPLE_RATE = 16000
const SPEECH_ACTIVATION_MS = 180

export const MEDIA_INSECURE_CONTEXT_ERROR = 'MEDIA_INSECURE_CONTEXT'
export const MEDIA_UNSUPPORTED_ERROR = 'MEDIA_UNSUPPORTED'

function float32ToPCM16(input: Float32Array): Int16Array {
  const output = new Int16Array(input.length)
  for (let i = 0; i < input.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, input[i]))
    output[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }
  return output
}

function pcmToBase64(pcm: Int16Array): string {
  const bytes = new Uint8Array(pcm.buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i += 1) {
    binary += String.fromCharCode(bytes[i])
  }
  return window.btoa(binary)
}

function downsampleBuffer(input: Float32Array, sourceRate: number, targetRate: number): Float32Array {
  if (targetRate >= sourceRate || sourceRate <= 0) {
    return input
  }

  const ratio = sourceRate / targetRate
  const outputLength = Math.max(1, Math.round(input.length / ratio))
  const output = new Float32Array(outputLength)

  let offsetResult = 0
  let offsetBuffer = 0
  while (offsetResult < outputLength) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio)
    let accum = 0
    let count = 0

    for (let i = offsetBuffer; i < nextOffsetBuffer && i < input.length; i += 1) {
      accum += input[i]
      count += 1
    }

    output[offsetResult] = count > 0 ? accum / count : 0
    offsetResult += 1
    offsetBuffer = nextOffsetBuffer
  }

  return output
}

export function useAudioRecorder({ onChunk, onSpeechStart, onSpeechEnd, enabled }: UseAudioRecorderParams): UseAudioRecorderResult {
  const [isRecording, setIsRecording] = useState(false)
  const [micLevel, setMicLevel] = useState(0)

  const audioContextRef = useRef<AudioContext | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const pcmBufferRef = useRef<number[]>([])
  const sourceSampleRateRef = useRef(TARGET_SAMPLE_RATE)
  const lastVoiceAtRef = useRef(0)
  const speechCandidateSinceRef = useRef(0)
  const speechStartedRef = useRef(false)
  const runningRef = useRef(false)
  const chunkTimerRef = useRef<number | null>(null)
  const onChunkRef = useRef(onChunk)
  const onSpeechStartRef = useRef(onSpeechStart)
  const onSpeechEndRef = useRef(onSpeechEnd)

  useEffect(() => {
    onChunkRef.current = onChunk
  }, [onChunk])

  useEffect(() => {
    onSpeechStartRef.current = onSpeechStart
  }, [onSpeechStart])

  useEffect(() => {
    onSpeechEndRef.current = onSpeechEnd
  }, [onSpeechEnd])

  const flushChunk = useCallback(() => {
    const values = pcmBufferRef.current
    if (values.length === 0) {
      return
    }
    pcmBufferRef.current = []

    const floatData = new Float32Array(values)
    const normalized = downsampleBuffer(floatData, sourceSampleRateRef.current, TARGET_SAMPLE_RATE)
    const pcm = float32ToPCM16(normalized)
    onChunkRef.current(pcmToBase64(pcm), TARGET_SAMPLE_RATE)
  }, [])

  const cleanup = useCallback(() => {
    if (chunkTimerRef.current) {
      window.clearInterval(chunkTimerRef.current)
      chunkTimerRef.current = null
    }

    processorRef.current?.disconnect()
    sourceRef.current?.disconnect()
    streamRef.current?.getTracks().forEach((track) => track.stop())

    if (audioContextRef.current) {
      void audioContextRef.current.close()
    }

    processorRef.current = null
    sourceRef.current = null
    streamRef.current = null
    audioContextRef.current = null
    pcmBufferRef.current = []
    speechStartedRef.current = false
    speechCandidateSinceRef.current = 0
    runningRef.current = false
    setMicLevel(0)
    setIsRecording(false)
  }, [])

  const stop = useCallback(() => {
    if (!runningRef.current) {
      return
    }
    cleanup()
  }, [cleanup])

  const start = useCallback(async () => {
    if (!enabled || runningRef.current) {
      return
    }

    const hostname = window.location.hostname
    const localHost = isPotentiallyTrustworthyHost(hostname)
    if (!window.isSecureContext && !localHost) {
      throw new Error(MEDIA_INSECURE_CONTEXT_ERROR)
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error(MEDIA_UNSUPPORTED_ERROR)
    }

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: TARGET_SAMPLE_RATE,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: false,
    })

    const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AudioContextCtor) {
      throw new Error('AudioContext is not supported in this browser')
    }

    const audioContext = new AudioContextCtor()
    const source = audioContext.createMediaStreamSource(stream)
    const processor = audioContext.createScriptProcessor(4096, 1, 1)

    sourceSampleRateRef.current = audioContext.sampleRate
    streamRef.current = stream
    audioContextRef.current = audioContext
    sourceRef.current = source
    processorRef.current = processor
    runningRef.current = true
    setIsRecording(true)
    speechStartedRef.current = false
    speechCandidateSinceRef.current = 0
    lastVoiceAtRef.current = Date.now()

    processor.onaudioprocess = (event) => {
      if (!runningRef.current) {
        return
      }

      const channel = event.inputBuffer.getChannelData(0)
      let sumSquares = 0
      for (let i = 0; i < channel.length; i += 1) {
        const value = channel[i]
        sumSquares += value * value
      }
      const rms = Math.sqrt(sumSquares / channel.length)
      setMicLevel(Math.min(1, rms * 8))

      const now = Date.now()
      if (rms > SILENCE_THRESHOLD) {
        if (!speechStartedRef.current) {
          if (!speechCandidateSinceRef.current) {
            speechCandidateSinceRef.current = now
          }
          if (now - speechCandidateSinceRef.current >= SPEECH_ACTIVATION_MS) {
            onSpeechStartRef.current?.()
            speechStartedRef.current = true
            lastVoiceAtRef.current = now
          }
        } else {
          lastVoiceAtRef.current = now
        }
      } else if (!speechStartedRef.current) {
        speechCandidateSinceRef.current = 0
      }

      if (speechStartedRef.current) {
        for (let i = 0; i < channel.length; i += 1) {
          pcmBufferRef.current.push(channel[i])
        }

        if (rms <= SILENCE_THRESHOLD && now - lastVoiceAtRef.current > MAX_SILENCE_MS) {
          flushChunk()
          onSpeechEndRef.current()
          speechStartedRef.current = false
          speechCandidateSinceRef.current = 0
          lastVoiceAtRef.current = now
        }
      }
    }

    source.connect(processor)
    processor.connect(audioContext.destination)

    chunkTimerRef.current = window.setInterval(() => {
      if (runningRef.current && pcmBufferRef.current.length > 0) {
        flushChunk()
      }
    }, CHUNK_MS)
  }, [enabled, flushChunk])

  useEffect(() => {
    return () => {
      cleanup()
    }
  }, [cleanup])

  return {
    isRecording,
    micLevel,
    start,
    stop,
  }
}
