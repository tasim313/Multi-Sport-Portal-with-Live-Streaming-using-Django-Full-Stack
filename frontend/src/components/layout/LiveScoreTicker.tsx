'use client'

import { useEffect, useRef } from 'react'
import Link from 'next/link'
import { useTickerStore } from '@/store/ticker'
import { createTickerWS } from '@/lib/websocket'
import type { TickerMatch } from '@/types'

export function LiveScoreTicker() {
  const { matches, setMatches, updateMatch } = useTickerStore()
  const wsRef = useRef<ReturnType<typeof createTickerWS> | null>(null)

  useEffect(() => {
    const ws = createTickerWS()
    wsRef.current = ws

    ws.on('ticker_data', (data) => setMatches(data as TickerMatch[]))
    ws.on('ticker_update', (data) => updateMatch(data as TickerMatch))

    ws.connect()

    return () => ws.disconnect()
  }, [setMatches, updateMatch])

  if (!matches.length) return null

  return (
    <div className="bg-zinc-900 border-b border-zinc-800 overflow-hidden">
      <div className="flex items-center">
        {/* LIVE label */}
        <div className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-red-600 text-white text-xs font-bold">
          <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse-fast" />
          LIVE
        </div>

        {/* Scrolling ticker */}
        <div className="overflow-hidden flex-1">
          <div className="ticker-scroll flex gap-8 py-1.5 px-4 animate-[ticker_30s_linear_infinite]"
            style={{
              animation: `ticker ${Math.max(matches.length * 5, 20)}s linear infinite`
            }}
          >
            {[...matches, ...matches].map((match, i) => (
              <Link
                key={`${match.id}-${i}`}
                href={`/matches/${match.id}`}
                className="flex-shrink-0 flex items-center gap-3 text-xs hover:text-red-400 transition-colors"
              >
                <span className="text-zinc-500 text-[10px] uppercase tracking-wide">{match.sport}</span>
                <span className="text-zinc-100 font-medium">{match.home}</span>
                <span className="font-bold text-sm bg-zinc-800 px-2 py-0.5 rounded">
                  {match.score?.home ?? 0} — {match.score?.away ?? 0}
                </span>
                <span className="text-zinc-100 font-medium">{match.away}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes ticker {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  )
}
