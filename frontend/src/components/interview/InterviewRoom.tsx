import { Mic, MicOff, Send, AlertCircle, Loader2, Mic2, Wifi, WifiOff } from 'lucide-react'
import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { useInterviewStore, type Message } from '@/stores/interviewStore'
import { ChatPanel } from './ChatPanel'
import { AudioPanel } from './AudioPanel'
import { AIVoiceAnimation } from './AIVoiceAnimation'
import { StatusBar } from './StatusBar'
import { Button } from '@/components/ui/Button'
import { Textarea } from '@/components/ui/Textarea'
import { Card, CardContent } from '@/components/ui/Card'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { useTTSPlayer } from '@/hooks/useTTSPlayer'
import { useManualVoiceInput } from '@/hooks/useManualVoiceInput'
import { useManualTTS } from '@/hooks/useManualTTS'
import { api, getMessages } from '@/services/api'

const localMessage = (params: Omit<Message, 'id' | 'timestamp'>): Message => ({
  ...params,
  id: crypto.randomUUID(),
  timestamp: new Date().toISOString(),
})

interface WsMessage {
  type: string
  [key: string]: unknown
}

export function InterviewRoom({ sessionId }: { sessionId: string }) {
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [micMutedByTts, setMicMutedByTts] = useState(false)
  const [ttsPlayingFor, setTtsPlayingFor] = useState<string | null>(null)
  const [manualVoiceActive, setManualVoiceActive] = useState(false)
  const [micPermission, setMicPermission] = useState<'pending' | 'granted' | 'denied'>('pending')
  const [requestingMic, setRequestingMic] = useState(false)
  const currentResponseIdRef = { current: '' }

  const {
    setSession,
    messages,
    setMessages,
    addMessage,
    stage,
    setStage,
    streamText,
    appendStreamToken,
    clearStreamText,
    sttPreview,
    setSttPreview,
    inputMode,
    setInputMode,
    ttsProviderLabel,
    setTtsProviderLabel,
    llmStats,
    setLlmStats,
    reset,
  } = useInterviewStore()

  const { playing: ttsPlaying, queueSize: ttsQueueSize, enqueueBase64, clear: clearTtsQueue } = useTTSPlayer({
    onQueueEmpty: () => setStage('listening'),
  })

  const { play: playManualTts, stop: stopManualTts, status: manualTtsStatus } = useManualTTS()

  const handleTranscriptReady = useCallback((text: string) => {
    if (text) {
      setInput((prev) => (prev.trim() ? prev + ' ' + text : text))
    }
  }, [])

  const { isRecording: isManualRecording, startRecording: startManualRecording, stopRecording: stopManualRecording } = useManualVoiceInput({
    sessionId,
    onTranscription: handleTranscriptReady,
  })

  const handleSocketMessage = useCallback((payload: Record<string, unknown>) => {
    const msg = payload as WsMessage
    switch (msg.type) {
      case 'stt_partial':
        setSttPreview(String(msg.text || ''))
        return
      case 'stt_final': {
        const text = String(msg.text || '').trim()
        setSttPreview(text)
        if (text) {
          currentResponseIdRef.current = ''
          clearStreamText()
          setLlmStats(null)
          const nextTurn = messages.filter((m) => m.role === 'candidate').length + 1
          addMessage(localMessage({ session_id: sessionId, role: 'candidate', content: text, turn_index: nextTurn }))
          setStage('thinking')
        }
        return
      }
      case 'llm_token': {
        const rid = String(msg.response_id || '')
        if (rid && !currentResponseIdRef.current) {
          currentResponseIdRef.current = rid
        }
        if (rid && currentResponseIdRef.current && rid !== currentResponseIdRef.current) {
          return
        }
        setStage('speaking')
        appendStreamToken(String(msg.token || ''))
        return
      }
      case 'llm_done': {
        const rid = String(msg.response_id || '')
        if (rid && rid !== currentResponseIdRef.current) return
        addMessage(localMessage({ session_id: sessionId, role: 'interviewer', content: String(msg.full_text || ''), turn_index: Number(msg.turn_index) || 1 }))
        clearStreamText()
        return
      }
      case 'llm_stats':
        setLlmStats(msg as unknown as typeof llmStats)
        return
      case 'tts_audio':
        enqueueBase64(String(msg.data || ''), String(msg.format || 'pcm_s16le'), Number(msg.sample_rate) || 22050)
        return
      case 'tts_done':
        if (!ttsPlaying && ttsQueueSize === 0) {
          setStage('listening')
        }
        return
      case 'tts_interrupted':
        clearTtsQueue()
        currentResponseIdRef.current = ''
        setStage('listening')
        setTtsProviderLabel('已打断')
        return
      case 'error':
        setStage('idle')
        return
    }
  }, [addMessage, appendStreamToken, clearStreamText, enqueueBase64, clearTtsQueue, messages, sessionId, setStage, setSttPreview, setLlmStats, setTtsProviderLabel, ttsPlaying, ttsQueueSize])

  const { send, sendAudioChunk, sendAudioEnd, sendInterrupt, connected } = useWebSocket({ sessionId, onMessage: handleSocketMessage })

  const recorderEnabled = connected && inputMode === 'voice'

  const { isRecording, stop, mute, unmute } = useAudioRecorder({
    enabled: recorderEnabled && !manualVoiceActive,
    onChunk: (chunk, sampleRate) => sendAudioChunk(chunk, sampleRate),
    onSpeechEnd: () => sendAudioEnd(),
  })

  useEffect(() => {
    api.get<{ id: string; job_role: string; sub_role?: string }>(`/sessions/${sessionId}`)
      .then(setSession)
      .catch(() => navigate('/'))
    getMessages(sessionId).then((msgs) => setMessages(msgs as Message[])).catch(() => {})
  }, [sessionId])

  useEffect(() => {
    if (inputMode !== 'voice') return
    if (ttsPlaying || ttsQueueSize > 0 || manualTtsStatus === 'playing') {
      mute()
      setMicMutedByTts(true)
    } else if (micMutedByTts) {
      unmute()
      setMicMutedByTts(false)
    }
  }, [ttsPlaying, ttsQueueSize, manualTtsStatus, inputMode, mute, unmute, micMutedByTts])

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(s => { s.getTracks().forEach(t => t.stop()); setMicPermission('granted') })
      .catch(() => setMicPermission('pending'))
  }, [])

  const requestMicPermission = async () => {
    setRequestingMic(true)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop())
      setMicPermission('granted')
    } catch {
      setMicPermission('denied')
    } finally {
      setRequestingMic(false)
    }
  }

  const handleSendText = () => {
    if (!input.trim()) return
    const text = input.trim()
    const nextTurn = messages.filter((m) => m.role === 'candidate').length + 1
    setLlmStats(null)
    currentResponseIdRef.current = ''
    if (stage === 'speaking' || stage === 'thinking') {
      sendInterrupt('text_override')
    }
    addMessage(localMessage({ session_id: sessionId, role: 'candidate', content: text, turn_index: nextTurn }))
    setStage('thinking')
    send({ type: 'candidate_message', text })
    setInput('')
  }

  const handleEnd = async () => {
    stop()
    stopManualRecording()
    stopManualTts()
    clearTtsQueue()
    reset()
    await api.patch(`/sessions/${sessionId}`, { status: 'completed' }).catch(() => {})
    navigate(`/report/${sessionId}`)
  }

  const handleReadAloud = useCallback((messageId: string, text: string) => {
    setTtsPlayingFor(messageId)
    playManualTts(messageId, text)
    setTimeout(() => {
      if (ttsPlayingFor === messageId) setTtsPlayingFor(null)
    }, 30000)
  }, [playManualTts, ttsPlayingFor])

  useEffect(() => {
    if (manualTtsStatus === 'idle') setTtsPlayingFor(null)
  }, [manualTtsStatus])

  const handleManualVoiceToggle = () => {
    if (manualVoiceActive) {
      stopManualRecording()
      setManualVoiceActive(false)
    } else {
      setManualVoiceActive(true)
      startManualRecording()
    }
  }

  const turnCount = messages.filter((m) => m.role === 'candidate').length

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-border bg-surface flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Mic2 size={18} className="text-primary" />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-widest text-text-muted">面试进行中</p>
            <p className="text-sm font-semibold text-text">AI 模拟面试</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
            connected
              ? 'bg-success/10 text-success'
              : 'bg-error/10 text-error'
          }`}>
            {connected ? <Wifi size={10} /> : <WifiOff size={10} />}
            {connected ? '已连接' : '未连接'}
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant={inputMode === 'voice' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => {
                if (inputMode !== 'voice') {
                  if (micPermission !== 'granted') {
                    requestMicPermission()
                  }
                  setInputMode('voice')
                }
              }}
              disabled={requestingMic}
              className="h-8 text-xs"
            >
              {requestingMic ? <Loader2 size={12} className="mr-1 animate-spin" /> : <Mic size={12} className="mr-1" />}
              语音模式
            </Button>
            <Button variant={inputMode === 'text' ? 'primary' : 'secondary'} size="sm" onClick={() => setInputMode('text')} className="h-8 text-xs">
              <MicOff size={12} className="mr-1" />文本模式
            </Button>
            <Button variant="outline" size="sm" onClick={handleEnd} className="h-8 text-xs">结束面试</Button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {inputMode === 'voice' && micPermission !== 'granted' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex items-center gap-2 px-4 py-2 bg-warning/10 border-b border-warning/20 text-xs flex-shrink-0"
          >
            <AlertCircle size={14} className="text-warning flex-shrink-0" />
            <span className="text-warning flex-1">
              {micPermission === 'denied' ? '麦克风权限被拒绝，请检查浏览器设置' : '正在请求麦克风权限...'}
            </span>
            {micPermission === 'denied' && (
              <Button variant="outline" size="sm" onClick={requestMicPermission} className="h-6 text-xs">重试</Button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[260px_1fr_260px] min-h-0 gap-0">
        <div className="hidden lg:flex flex-col p-3 border-r border-border bg-surface/50">
          <AudioPanel level={0} active={isRecording || isManualRecording} />
        </div>

        <div className="flex flex-col min-h-0 overflow-hidden p-3 gap-3">
          {inputMode === 'voice' ? (
            <div className="flex-1 flex items-center justify-center rounded-2xl border border-border bg-surface min-h-[180px]">
              <AIVoiceAnimation stage={stage as 'thinking' | 'speaking'} />
            </div>
          ) : (
            <div className="flex-1 min-h-0">
              <ChatPanel
                messages={messages}
                streamText={streamText}
                onReadAloud={handleReadAloud}
                ttsPlayingFor={ttsPlayingFor}
                inputMode={inputMode}
                stage={stage}
              />
            </div>
          )}

          <AnimatePresence>
            {inputMode === 'text' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <Card className="border border-border bg-surface">
                  <CardContent className="flex items-end gap-2 p-3">
                    <Textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendText()
                        }
                      }}
                      placeholder="输入你的回答..."
                      disabled={!connected}
                      className="flex-1 min-h-[60px] max-h-[120px] resize-none text-sm"
                    />
                    <div className="flex flex-col gap-1.5">
                      <Button
                        variant={manualVoiceActive ? 'primary' : 'secondary'}
                        size="sm"
                        onClick={handleManualVoiceToggle}
                        className="h-8 w-8 p-0"
                      >
                        <Mic size={14} />
                      </Button>
                      <Button
                        onClick={handleSendText}
                        disabled={!input.trim() || !connected}
                        className="h-8"
                      >
                        <Send size={14} />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="hidden lg:flex flex-col p-3 border-l border-border bg-surface/50">
          <StatusBar
            stage={stage}
            connected={connected}
            turnCount={turnCount}
            sttPreview={sttPreview}
            ttsQueueSize={ttsQueueSize}
            recording={isRecording}
            ttsProviderLabel={ttsProviderLabel}
            llmStats={llmStats}
          />
        </div>
        </div>
    </div>
  )
}
