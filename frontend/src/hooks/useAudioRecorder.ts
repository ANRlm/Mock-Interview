import { useRef, useState, useCallback, useEffect } from 'react'

interface UseAudioRecorderOptions {
  enabled?: boolean
  onChunk?: (chunk: ArrayBuffer, sampleRate: number) => void
  onSpeechEnd?: () => void
}

export function useAudioRecorder({ enabled = false, onChunk }: UseAudioRecorderOptions = {}) {
  const [isRecording, setIsRecording] = useState(false)
  const [micLevel, setMicLevel] = useState(0)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const animationRef = useRef<number | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamDestRef = useRef<MediaStreamAudioDestinationNode | null>(null)

  const start = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const ctx = new AudioContext()
      audioContextRef.current = ctx
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      analyserRef.current = analyser

      const dest = ctx.createMediaStreamDestination()
      source.connect(dest)
      streamDestRef.current = dest

      const recorder = new MediaRecorder(dest.stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        blob.arrayBuffer().then((buffer) => {
          onChunk?.(buffer, 16000)
        })
        chunksRef.current = []
      }

      recorder.start(50)
      setIsRecording(true)

      const updateLevel = () => {
        if (!analyserRef.current) return
        const data = new Uint8Array(analyserRef.current.frequencyBinCount)
        analyserRef.current.getByteFrequencyData(data)
        const avg = data.reduce((a, b) => a + b, 0) / data.length
        setMicLevel((avg / 128) * 100)
        animationRef.current = requestAnimationFrame(updateLevel)
      }
      updateLevel()
    } catch {
      setIsRecording(false)
    }
  }, [onChunk])

  const stop = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    // Close AudioContext to release hardware resources
    if (audioContextRef.current?.state !== 'closed') {
      audioContextRef.current?.close()
    }
    audioContextRef.current = null
    analyserRef.current = null
    setIsRecording(false)
    setMicLevel(0)
  }, [])

  const mute = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => { t.enabled = false })
  }, [])

  const unmute = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => { t.enabled = true })
  }, [])

  useEffect(() => {
    if (!enabled) {
      stop()
    }
  }, [enabled, stop])

  useEffect(() => {
    return () => {
      stop()
    }
  }, [stop])

  return { isRecording, micLevel, start, stop, mute, unmute }
}