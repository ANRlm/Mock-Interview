'use client'

interface AIVoiceAnimationProps {
  stage: 'thinking' | 'speaking'
}

export function AIVoiceAnimation({ stage }: AIVoiceAnimationProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px]">
      <div className="relative flex items-center justify-center w-20 h-20">
        {stage === 'thinking' ? (
          <div className="flex gap-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-4 h-4 bg-primary dark:bg-primary rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s`, animationDuration: '0.8s' }}
              />
            ))}
          </div>
        ) : (
          <div className="relative flex items-center justify-center">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="absolute w-full h-full border-2 border-primary dark:border-primary rounded-full animate-ping opacity-25"
                style={{ animationDelay: `${i * 0.4}s`, animationDuration: '1.5s' }}
              />
            ))}
            <div className="w-6 h-6 bg-primary dark:bg-primary rounded-full z-10" />
          </div>
        )}
      </div>
      <p className="mt-4 text-sm text-text-muted">
        {stage === 'thinking' ? 'AI 思考中...' : 'AI 回答中...'}
      </p>
    </div>
  )
}