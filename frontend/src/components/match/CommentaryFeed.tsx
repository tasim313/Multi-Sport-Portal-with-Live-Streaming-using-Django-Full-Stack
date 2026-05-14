'use client'

import { useEffect, useRef, useState } from 'react'
import { format } from 'date-fns'
import { createMatchWS } from '@/lib/websocket'
import type { LiveCommentary } from '@/types'

interface CommentaryFeedProps {
  matchId: number
  initialCommentary?: LiveCommentary[]
}

interface CommentaryMessage {
  minute: number | null
  period: string
  text: string
  is_key: boolean
  event_type?: string
  created_at?: string
}

export function CommentaryFeed({ matchId, initialCommentary = [] }: CommentaryFeedProps) {
  const [commentary, setCommentary] = useState<CommentaryMessage[]>(
    initialCommentary.map(c => ({
      minute: c.minute,
      period: c.period,
      text: c.rewritten_text,
      is_key: c.is_key_event,
      created_at: c.created_at,
    }))
  )
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const ws = createMatchWS(matchId)

    ws.on('commentary_history', (data) => {
      const msgs = data as CommentaryMessage[]
      setCommentary(msgs.reverse())
    })

    ws.on('commentary_update', (data) => {
      const msg = data as CommentaryMessage
      setCommentary(prev => [msg, ...prev])
      // Flash scroll to top on new entry
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    })

    ws.connect()
    return () => ws.disconnect()
  }, [matchId])

  return (
    <div className="flex flex-col gap-2 max-h-96 overflow-y-auto">
      <div ref={bottomRef} />
      {commentary.length === 0 && (
        <p className="text-zinc-500 text-sm text-center py-4">
          Commentary will appear here during the match.
        </p>
      )}
      {commentary.map((c, i) => (
        <div
          key={i}
          className={`flex gap-3 p-3 rounded-lg transition-all duration-300 animate-fade-in ${
            c.is_key
              ? 'bg-red-950/40 border border-red-900/50'
              : 'bg-zinc-900/50'
          }`}
        >
          {/* Minute indicator */}
          <div className="flex-shrink-0 w-10 text-center">
            {c.minute !== null ? (
              <span className={`text-xs font-bold ${c.is_key ? 'text-red-400' : 'text-zinc-500'}`}>
                {c.minute}&apos;
              </span>
            ) : (
              <span className="text-xs text-zinc-600">—</span>
            )}
          </div>

          {/* Text */}
          <p className={`text-sm leading-relaxed flex-1 ${c.is_key ? 'text-zinc-100 font-medium' : 'text-zinc-300'}`}>
            {c.is_key && (
              <span className="inline-block w-2 h-2 bg-red-500 rounded-full mr-2 align-middle" />
            )}
            {c.text}
          </p>
        </div>
      ))}
    </div>
  )
}
