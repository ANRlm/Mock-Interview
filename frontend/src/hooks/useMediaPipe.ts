import { useCallback, useEffect, useRef, useState } from 'react'

export interface BehaviorFrameSample {
  frameSecond: number
  eyeContactScore: number
  headPoseScore: number
  gazeX: number
  gazeY: number
  imageBase64: string | null
}

interface UseMediaPipeResult {
  ready: boolean
  cameraEnabled: boolean
  eyeContactScore: number
  headPoseScore: number
  gazeX: number
  gazeY: number
  expression: string
  warning: string | null
  start: () => Promise<void>
  stop: () => void
  captureFrame: (frameSecond: number) => BehaviorFrameSample | null
}

export const CAMERA_INSECURE_CONTEXT_ERROR = 'CAMERA_INSECURE_CONTEXT'
export const CAMERA_UNSUPPORTED_ERROR = 'CAMERA_UNSUPPORTED'

export function isPotentiallyTrustworthyHost(hostname: string): boolean {
  if (!hostname) {
    return false
  }
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1') {
    return true
  }
  if (hostname.endsWith('.localhost')) {
    return true
  }
  if (/^127(?:\.\d{1,3}){3}$/.test(hostname)) {
    return true
  }
  if (/^\[?::1\]?$/.test(hostname)) {
    return true
  }
  return false
}

const IDEAL_CONSTRAINTS = {
  video: {
    width: { ideal: 640 },
    height: { ideal: 360 },
    facingMode: 'user',
  },
  audio: false,
}

function clamp01(value: number): number {
  if (value < 0) {
    return 0
  }
  if (value > 1) {
    return 1
  }
  return value
}

function averageLuma(imageData: ImageData): number {
  const data = imageData.data
  const step = Math.max(1, Math.floor(data.length / (4 * 3000)))
  let total = 0
  let count = 0
  for (let i = 0; i < data.length; i += 4 * step) {
    const r = data[i]
    const g = data[i + 1]
    const b = data[i + 2]
    total += 0.299 * r + 0.587 * g + 0.114 * b
    count += 1
  }
  if (count === 0) {
    return 0
  }
  return total / count
}

function estimateScores(imageData: ImageData): {
  eyeContact: number
  headPose: number
  gazeX: number
  gazeY: number
  expression: string
} {
  const width = imageData.width
  const height = imageData.height
  const data = imageData.data

  let leftLuma = 0
  let rightLuma = 0
  let topLuma = 0
  let bottomLuma = 0
  let leftCount = 0
  let rightCount = 0
  let topCount = 0
  let bottomCount = 0

  const sampleStep = 10
  for (let y = 0; y < height; y += sampleStep) {
    for (let x = 0; x < width; x += sampleStep) {
      const idx = (y * width + x) * 4
      const luma = 0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2]

      if (x < width / 2) {
        leftLuma += luma
        leftCount += 1
      } else {
        rightLuma += luma
        rightCount += 1
      }

      if (y < height / 2) {
        topLuma += luma
        topCount += 1
      } else {
        bottomLuma += luma
        bottomCount += 1
      }
    }
  }

  const leftAvg = leftCount ? leftLuma / leftCount : 0
  const rightAvg = rightCount ? rightLuma / rightCount : 0
  const topAvg = topCount ? topLuma / topCount : 0
  const bottomAvg = bottomCount ? bottomLuma / bottomCount : 0

  const horizontalDiff = rightAvg - leftAvg
  const verticalDiff = bottomAvg - topAvg

  const gazeX = clamp01(0.5 + horizontalDiff / 120)
  const gazeY = clamp01(0.5 + verticalDiff / 120)

  const eyeContact = clamp01(1 - Math.abs(gazeX - 0.5) * 1.8)
  const headPose = clamp01(1 - (Math.abs(horizontalDiff) + Math.abs(verticalDiff)) / 180)

  const brightness = averageLuma(imageData)
  let expression = 'neutral'
  if (brightness > 160 && eyeContact > 0.68) {
    expression = 'engaged'
  } else if (brightness < 90 && headPose < 0.5) {
    expression = 'tired'
  } else if (eyeContact < 0.4) {
    expression = 'distracted'
  }

  return {
    eyeContact,
    headPose,
    gazeX,
    gazeY,
    expression,
  }
}

export function useMediaPipe(): UseMediaPipeResult {
  const [ready, setReady] = useState(false)
  const [cameraEnabled, setCameraEnabled] = useState(false)
  const [warning, setWarning] = useState<string | null>(null)
  const [eyeContactScore, setEyeContactScore] = useState(0)
  const [headPoseScore, setHeadPoseScore] = useState(0)
  const [gazeX, setGazeX] = useState(0.5)
  const [gazeY, setGazeY] = useState(0.5)
  const [expression, setExpression] = useState('neutral')

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stop = useCallback(() => {
    const stream = streamRef.current
    if (stream) {
      for (const track of stream.getTracks()) {
        track.stop()
      }
    }
    streamRef.current = null
    setReady(false)
    setCameraEnabled(false)
  }, [])

  const start = useCallback(async () => {
    const hostname = window.location.hostname
    const localHost = isPotentiallyTrustworthyHost(hostname)
    if (!window.isSecureContext && !localHost) {
      setWarning(CAMERA_INSECURE_CONTEXT_ERROR)
      return
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setWarning(CAMERA_UNSUPPORTED_ERROR)
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia(IDEAL_CONSTRAINTS)
      streamRef.current = stream

      if (!videoRef.current) {
        videoRef.current = document.createElement('video')
        videoRef.current.muted = true
        videoRef.current.playsInline = true
      }

      const video = videoRef.current
      video.srcObject = stream
      await video.play()

      if (!canvasRef.current) {
        canvasRef.current = document.createElement('canvas')
      }

      setWarning(null)
      setReady(true)
      setCameraEnabled(true)
    } catch (error) {
      stop()
      setWarning(error instanceof Error ? error.message : '摄像头启动失败')
    }
  }, [stop])

  const captureFrame = useCallback((frameSecond: number): BehaviorFrameSample | null => {
    if (!ready || !videoRef.current || !canvasRef.current) {
      return null
    }

    const video = videoRef.current
    const canvas = canvasRef.current
    if (video.videoWidth < 2 || video.videoHeight < 2) {
      return null
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) {
      return null
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const scores = estimateScores(imageData)

    setEyeContactScore(scores.eyeContact)
    setHeadPoseScore(scores.headPose)
    setGazeX(scores.gazeX)
    setGazeY(scores.gazeY)
    setExpression(scores.expression)

    return {
      frameSecond,
      eyeContactScore: scores.eyeContact,
      headPoseScore: scores.headPose,
      gazeX: scores.gazeX,
      gazeY: scores.gazeY,
      imageBase64: null,
    }
  }, [ready])

  useEffect(() => {
    return () => {
      stop()
    }
  }, [stop])

  return {
    ready,
    cameraEnabled,
    eyeContactScore,
    headPoseScore,
    gazeX,
    gazeY,
    expression,
    warning,
    start,
    stop,
    captureFrame,
  }
}
