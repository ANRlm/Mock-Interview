import { useCallback, useEffect, useMemo, useState } from 'react'
import { Mic, MicOff, Send } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { AudioVisualizer } from '@/components/interview/AudioVisualizer'
import { ChatPanel } from '@/components/interview/ChatPanel'
import { StatusBar } from '@/components/interview/StatusBar'
import { VideoPanel } from '@/components/interview/VideoPanel'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { useMediaPipe } from '@/hooks/useMediaPipe'
import { useTTSPlayer } from '@/hooks/useTTSPlayer'
import { useWebSocket } from '@/hooks/useWebSocket'
import { getMessages, postBehavior, updateSession } from '@/services/api'
import { useInterviewStore } from '@/stores/interviewStore'
import { useSettingsStore } from '@/stores/settingsStore'
import type { ConversationMessage, TtsProvider, WsServerMessage } from '@/types/interview'

const localMessage = (params: Omit<ConversationMessage, 'id' | 'timestamp'>): ConversationMessage => ({
  ...params,
  id: crypto.randomUUID(),
  timestamp: new Date().toISOString(),
})

export function InterviewRoom() {
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [micDenied, setMicDenied] = useState(false)

  const { selectedRole, subRole } = useSettingsStore()
  const {
    session,
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
    setTtsProvider,
    setTtsProviderLabel,
    llmStats,
    setLlmStats,
  } = useInterviewStore()

  const sessionId = session?.id ?? null

  const { playing: ttsPlaying, queueSize: ttsQueueSize, enqueueBase64, clear: clearTtsQueue } = useTTSPlayer(() => {
    setStage('listening')
  })

  const resolveProviderLabel = (provider: TtsProvider): string => {
    if (provider === 'cosyvoice2-http') {
      return 'CosyVoice2'
    }
    return '未知'
  }

  const handleSocketMessage = useCallback((payload: WsServerMessage) => {
    if (!session) {
      return
    }

    switch (payload.type) {
      case 'stt_partial': {
        setSttPreview(payload.text)
        return
      }
      case 'stt_final': {
        const candidateText = payload.text.trim()
        setSttPreview(payload.text)
        if (candidateText) {
          setLlmStats(null)
          const nextTurn = messages.filter((msg) => msg.role === 'candidate').length + 1
          addMessage(
            localMessage({
              session_id: session.id,
              role: 'candidate',
              content: candidateText,
              turn_index: nextTurn,
            }),
          )
          setStage('thinking')
        }
        return
      }
      case 'llm_token': {
        setStage('speaking')
        appendStreamToken(payload.token)
        return
      }
      case 'llm_done': {
        addMessage(
          localMessage({
            session_id: session.id,
            role: 'interviewer',
            content: payload.full_text,
            turn_index: payload.turn_index,
          }),
        )
        clearStreamText()
        return
      }
      case 'llm_stats': {
        setLlmStats(payload)
        return
      }
      case 'tts_audio': {
        const provider = payload.provider ?? 'unknown'
        setTtsProvider(provider)
        setTtsProviderLabel(resolveProviderLabel(provider))
        enqueueBase64(payload.data, payload.format)
        return
      }
      case 'tts_done': {
        if (!ttsPlaying && ttsQueueSize === 0) {
          setStage('listening')
        }
        return
      }
      case 'tts_interrupted': {
        clearTtsQueue()
        setStage('listening')
        setTtsProviderLabel('已打断')
        return
      }
      case 'error': {
        setStage('idle')
        return
      }
      case 'pong':
      case 'interview_end': {
        return
      }
      default: {
        return
      }
    }
  }, [addMessage, appendStreamToken, clearStreamText, enqueueBase64, clearTtsQueue, messages, session, setStage, setSttPreview, setLlmStats, setTtsProvider, setTtsProviderLabel, ttsPlaying, ttsQueueSize])

  const { sendCandidateMessage, sendAudioChunk, sendAudioEnd, sendInterrupt, connected } = useWebSocket({
    sessionId,
    onMessage: handleSocketMessage,
  })

  const mediaPipe = useMediaPipe()

  const interruptPlayback = useCallback(
    (reason = 'barge_in') => {
      clearTtsQueue()
      setTtsProviderLabel('已打断')
      setStage('listening')
      sendInterrupt(reason)
    },
    [clearTtsQueue, sendInterrupt, setStage, setTtsProviderLabel],
  )

  const recorderEnabled = connected && inputMode === 'voice'

  const { isRecording, micLevel, start, stop } = useAudioRecorder({
    enabled: recorderEnabled,
    onSpeechStart: () => {
      if (stage === 'speaking' || stage === 'thinking') {
        interruptPlayback('barge_in')
      }
    },
    onChunk: (chunk, sampleRate) => {
      sendAudioChunk(chunk, sampleRate)
    },
    onSpeechEnd: () => {
      sendAudioEnd()
    },
  })

  useEffect(() => {
    if (!sessionId) {
      return
    }

    getMessages(sessionId)
      .then((history) => setMessages(history))
      .catch(() => undefined)
  }, [sessionId, setMessages])

  useEffect(() => {
    if (!sessionId) {
      mediaPipe.stop()
      return
    }

    let disposed = false
    mediaPipe.start().catch(() => undefined)

    const timer = window.setInterval(() => {
      if (disposed || !sessionId) {
        return
      }

      const frameSecond = Math.floor(Date.now() / 1000)
      const sample = mediaPipe.captureFrame(frameSecond)
      if (!sample) {
        return
      }

      void postBehavior(sessionId, {
        frames: [
          {
            frame_second: sample.frameSecond,
            eye_contact_score: sample.eyeContactScore,
            head_pose_score: sample.headPoseScore,
            gaze_x: sample.gazeX,
            gaze_y: sample.gazeY,
            image_base64: sample.imageBase64,
          },
        ],
      }).catch(() => undefined)
    }, 5000)

    return () => {
      disposed = true
      window.clearInterval(timer)
      mediaPipe.stop()
    }
  }, [mediaPipe, sessionId])

  useEffect(() => {
    if (!recorderEnabled) {
      stop()
      return
    }

    start().catch(() => {
      setMicDenied(true)
      setInputMode('text')
      setStage('idle')
    })
  }, [recorderEnabled, setInputMode, setStage, start, stop])

  const turnCount = useMemo(() => messages.filter((msg) => msg.role === 'candidate').length, [messages])

  const handleSendText = () => {
    if (!session || !input.trim()) {
      return
    }

    const text = input.trim()
    const nextTurn = turnCount + 1

    setLlmStats(null)

    if (stage === 'speaking' || stage === 'thinking') {
      interruptPlayback('text_override')
    }

    addMessage(
      localMessage({
        session_id: session.id,
        role: 'candidate',
        content: text,
        turn_index: nextTurn,
      }),
    )

    setStage('thinking')
    sendCandidateMessage(text)
    setInput('')
  }

  const handleEnd = async () => {
    if (!session) {
      return
    }

    stop()
    clearTtsQueue()
    const updated = await updateSession(session.id, { status: 'completed' })
    setSession(updated)
    navigate(`/report/${session.id}`)
  }

  if (!session) {
    return (
      <Card>
        <CardContent className="flex items-center justify-between gap-4 p-8">
          <p className="text-sm text-slate-300">尚未创建面试会话，请先完成配置。</p>
          <Button onClick={() => navigate('/setup')}>前往配置页</Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-400">Interview Session</p>
          <p className="text-sm font-semibold text-slate-100">
            {selectedRole} {subRole ? `· ${subRole}` : ''}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={inputMode === 'voice' ? 'default' : 'secondary'}
            onClick={() => {
              setInputMode('voice')
              setStage('listening')
            }}
          >
            <Mic size={14} className="mr-1" />
            语音模式
          </Button>
          <Button
            variant={inputMode === 'text' ? 'default' : 'secondary'}
            onClick={() => {
              setInputMode('text')
              interruptPlayback('switch_to_text')
              stop()
              setStage('idle')
            }}
          >
            <MicOff size={14} className="mr-1" />
            文本模式
          </Button>
          <Button variant="outline" onClick={handleEnd}>
            结束并生成报告
          </Button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.05fr_1.35fr_0.9fr]">
        <div className="space-y-4">
          <VideoPanel
            ready={mediaPipe.ready}
            eyeContactScore={mediaPipe.eyeContactScore}
            headPoseScore={mediaPipe.headPoseScore}
            expression={mediaPipe.expression}
            warning={mediaPipe.warning}
          />
          <AudioVisualizer level={micLevel} active={isRecording} />
        </div>

        <ChatPanel messages={messages} streamText={streamText} />

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

      <Card>
        <CardContent className="space-y-3 p-4">
          <p className="text-xs text-slate-400">
            {inputMode === 'voice' ? '当前为语音模式，系统自动进行录音与静音检测。' : '当前为文本模式，可手动输入回答。'}
          </p>
          {micDenied ? <p className="text-xs text-amber-300">麦克风权限不可用，已自动切换到文本模式。</p> : null}
          <Textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="例如：我曾主导一个高并发系统改造，核心目标是..."
            disabled={inputMode !== 'text'}
          />
          <div className="flex justify-end">
            <Button onClick={handleSendText} disabled={inputMode !== 'text' || !input.trim() || !connected}>
              <Send size={14} className="mr-1" />
              发送回答
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
