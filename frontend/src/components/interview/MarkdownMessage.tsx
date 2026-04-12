import ReactMarkdown from 'react-markdown'

interface MarkdownMessageProps {
  content: string
  streaming?: boolean
}

export function MarkdownMessage({ content, streaming = false }: MarkdownMessageProps) {
  return (
    <div className="prose prose-invert prose-sm max-w-none text-sm leading-relaxed break-words">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="my-1.5 whitespace-pre-wrap">{children}</p>,
          ul: ({ children }) => <ul className="my-2 list-disc pl-5">{children}</ul>,
          ol: ({ children }) => <ol className="my-2 list-decimal pl-5">{children}</ol>,
          li: ({ children }) => <li className="my-0.5">{children}</li>,
          code: ({ className, children }) => {
            const text = String(children)
            const inline = !String(className || '').includes('language-') && !text.includes('\n')
            return inline ? (
              <code className="rounded bg-slate-900/80 px-1 py-0.5 text-[0.92em]">{children}</code>
            ) : (
              <code className="block whitespace-pre-wrap rounded-lg bg-slate-950/90 p-2 text-[0.9em]">{children}</code>
            )
          },
          pre: ({ children }) => <pre className="my-2 overflow-x-auto">{children}</pre>,
          blockquote: ({ children }) => <blockquote className="my-2 border-l-2 border-slate-600 pl-3 text-slate-300">{children}</blockquote>,
        }}
      >
        {content}
      </ReactMarkdown>
      {streaming ? <span className="ml-1 inline-block h-4 w-[2px] animate-pulse bg-cyan-300 align-middle" /> : null}
    </div>
  )
}
