import { Mic, MicOff, Send } from 'lucide-react'
import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInterviewStore, type Message } from '@/stores/interviewStore'
import { ChatPanel } from './ChatPanel'
import { AudioPanel } from './AudioPanel'
import { AIVoiceAnimation } from './AIVoiceAnimation'
import { StatusBar } from './StatusBar'
import { PosePip } from './PosePip'
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
    <div className="space-y-4">
      <PosePip />

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-surface px-4 py-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-text-muted">面试进行中</p>
          <p className="text-sm font-medium text-text">AI 模拟面试</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant={inputMode === 'voice' ? 'primary' : 'secondary'} size="sm" onClick={() => setInputMode('voice')}>
            <Mic size={14} className="mr-1" />语音模式
          </Button>
          <Button variant={inputMode === 'text' ? 'primary' : 'secondary'} size="sm" onClick={() => setInputMode('text')}>
            <MicOff size={14} className="mr-1" />文本模式
          </Button>
          <Button variant="secondary" size="sm" onClick={handleEnd}>结束面试</Button>
        </div>
      </div>

{inputMode === 'voice' ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_2fr_1fr]">
          <AudioPanel level={0} active={isRecording || isManualRecording} />
          <div className="flex items-center justify-center rounded-xl border border-border bg-surface">
            <AIVoiceAnimation stage={stage as 'thinking' | 'speaking'} />
          </div>
          <StatusBar stage={stage} connected={connected} turnCount={turnCount} sttPreview={sttPreview} ttsQueueSize={ttsQueueSize} recording={isRecording} ttsProviderLabel={ttsProviderLabel} llmStats={llmStats} />
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[1fr_2fr_1fr]">
          <AudioPanel level={0} active={isRecording || isManualRecording} />
          <ChatPanel messages={messages} streamText={streamText} onReadAloud={inputMode === 'text' ? handleReadAloud : undefined} ttsPlayingFor={ttsPlayingFor} inputMode={inputMode} stage={stage} />
          <StatusBar stage={stage} connected={connected} turnCount={turnCount} sttPreview={sttPreview} ttsQueueSize={ttsQueueSize} recording={isRecording} ttsProviderLabel={ttsProviderLabel} llmStats={llmStats} />
        </div>
      )}

      {inputMode === 'text' && (
        <Card>
          <CardContent className="space-y-3 p-4">
            <p className="text-xs text-text-muted">
              当前为文本模式，可手动输入回答。点击回复旁的"朗读"按钮可手动触发语音。点击下方麦克风图标可进行语音输入。
            </p>
            <div className="relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入你的回答..."
                disabled={inputMode !== 'text'}
                className="pr-20"
              />
              <div className="absolute bottom-2 right-2 flex gap-1">
                <Button variant={manualVoiceActive ? 'primary' : 'secondary'} size="sm" onClick={handleManualVoiceToggle} className="h-8 px-2">
                  <Mic size={14} />
                  <span className="ml-1 text-xs">语音</span>
                </Button>
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleSendText} disabled={!input.trim() || !connected}>
                <Send size={14} className="mr-1" />发送
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}