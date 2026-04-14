import { useRef, useState, useCallback } from 'react'
import { useAuthStore } from '@/stores/authStore'

interface UseManualVoiceInputOptions {
  sessionId: string
  onTranscription: (text: string) => void
}

export function useManualVoiceInput({ sessionId, onTranscription }: UseManualVoiceInputOptions) {
  const [isRecording, setIsRecording] = useState(false)
  const [isConverting, setIsConverting] = useState(false)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const token = useAuthStore((s) => s.token)

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = async () => {
        setIsConverting(true)
        try {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
          const formData = new FormData()
          formData.append('file', blob, 'audio.webm')

          const res = await fetch(`/api/sessions/${sessionId}/transcribe`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          })

          if (res.ok) {
            const data = await res.json()
            onTranscription(data.text || '')
          }
        } catch {
        } finally {
          setIsConverting(false)
          streamRef.current?.getTracks().forEach((t) => t.stop())
        }
      }

      recorder.start()
      setIsRecording(true)
    } catch {
      setIsRecording(false)
    }
  }, [sessionId, token, onTranscription])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    setIsRecording(false)
  }, [])

  return { isRecording, isConverting, startRecording, stopRecording }
}