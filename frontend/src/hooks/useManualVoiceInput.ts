import { useCallback, useEffect, useRef, useState } from 'react'

import { isPotentiallyTrustworthyHost } from '@/hooks/useMediaPipe'

interface UseManualVoiceInputResult {
  isRecording: boolean
  isConverting: boolean
  startRecording: () => Promise<void>
  stopRecording: () => void
}

const CHUNK_MS = 120
const SILENCE_THRESHOLD = 0.016
const MAX_SILENCE_MS = 1500
const TARGET_SAMPLE_RATE = 16000
const SPEECH_ACTIVATION_MS = 180

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

export function useManualVoiceInput(
  sessionId: string | null,
  onTranscriptReady: (text: string) => void,
): UseManualVoiceInputResult {
  const [isRecording, setIsRecording] = useState(false)
  const [isConverting, setIsConverting] = useState(false)

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
  const onTranscriptReadyRef = useRef(onTranscriptReady)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    onTranscriptReadyRef.current = onTranscriptReady
  }, [onTranscriptReady])

  const flushChunk = useCallback(() => {
    const values = pcmBufferRef.current
    if (values.length === 0) {
      return
    }
    pcmBufferRef.current = []

    const floatData = new Float32Array(values)
    const normalized = downsampleBuffer(floatData, sourceSampleRateRef.current, TARGET_SAMPLE_RATE)
    const pcm = float32ToPCM16(normalized)

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'audio_chunk',
        data: pcmToBase64(pcm),
        sample_rate: TARGET_SAMPLE_RATE,
      }))
    }
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
    setIsRecording(false)
  }, [])

  const stopRecording = useCallback(() => {
    if (!runningRef.current) {
      return
    }

    flushChunk()

    if (wsRef.current) {
      wsRef.current.send(JSON.stringify({ type: 'audio_end' }))
    }

    cleanup()
  }, [cleanup, flushChunk])

  const startRecording = useCallback(async () => {
    if (runningRef.current || !sessionId) {
      return
    }

    const hostname = window.location.hostname
    const localHost = isPotentiallyTrustworthyHost(hostname)
    if (!window.isSecureContext && !localHost) {
      return
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      return
    }

    try {
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
        return
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
      setIsConverting(false)
      speechStartedRef.current = false
      speechCandidateSinceRef.current = 0
      lastVoiceAtRef.current = Date.now()

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      const token = localStorage.getItem('auth-storage')
      let tokenValue = ''
      try {
        if (token) {
          const parsed = JSON.parse(token)
          tokenValue = parsed.state?.token || ''
        }
      } catch {}

      const ws = new WebSocket(`${protocol}//${host}/ws/stt/${sessionId}?token=${tokenValue}`)
      wsRef.current = ws

      ws.onopen = () => {}
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'stt_final' && data.text) {
            setIsConverting(true)
            onTranscriptReadyRef.current(data.text.trim())
            setIsConverting(false)
          } else if (data.type === 'stt_partial') {
          }
        } catch {}
      }
      ws.onerror = () => {
        setIsConverting(false)
      }
      ws.onclose = () => {
        setIsConverting(false)
        wsRef.current = null
      }

      processor.onaudioprocess = (event) => {
        if (!runningRef.current) {
          return
        }

        const channel = event.inputBuffer.getChannelData(0)
        const now = Date.now()

        if (speechStartedRef.current) {
          for (let i = 0; i < channel.length; i += 1) {
            pcmBufferRef.current.push(channel[i])
          }

          let sumSquares = 0
          for (let i = 0; i < channel.length; i += 1) {
            sumSquares += channel[i] * channel[i]
          }
          const rms = Math.sqrt(sumSquares / channel.length)

          if (rms <= SILENCE_THRESHOLD && now - lastVoiceAtRef.current > MAX_SILENCE_MS) {
            flushChunk()
            speechStartedRef.current = false
            speechCandidateSinceRef.current = 0
          }
        } else {
          let sumSquares = 0
          for (let i = 0; i < channel.length; i += 1) {
            sumSquares += channel[i] * channel[i]
          }
          const rms = Math.sqrt(sumSquares / channel.length)

          if (rms > SILENCE_THRESHOLD) {
            if (!speechCandidateSinceRef.current) {
              speechCandidateSinceRef.current = now
            }
            if (now - speechCandidateSinceRef.current >= SPEECH_ACTIVATION_MS) {
              speechStartedRef.current = true
              lastVoiceAtRef.current = now
            }
          }
        }
      }

      source.connect(processor)
      processor.connect(audioContext.destination)

      chunkTimerRef.current = window.setInterval(() => {
        if (runningRef.current && pcmBufferRef.current.length > 0 && speechStartedRef.current) {
          flushChunk()
        }
      }, CHUNK_MS)
    } catch {}
  }, [sessionId, flushChunk])

  useEffect(() => {
    return () => {
      cleanup()
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [cleanup])

  return {
    isRecording,
    isConverting,
    startRecording,
    stopRecording,
  }
}
