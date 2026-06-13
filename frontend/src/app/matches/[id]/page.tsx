'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { matchApi } from '@/lib/api'
import { VideoPlayer } from '@/components/match/VideoPlayer'
import { CommentaryFeed } from '@/components/match/CommentaryFeed'
import { createMatchWS } from '@/lib/websocket'
import { format } from 'date-fns'
import { Tv, MessageSquare, BarChart2, List } from 'lucide-react'
import type { ScoreEvent } from '@/types'

const DETAIL_TABS = [
  { key: 'stream', label: 'Stream', icon: Tv },
  { key: 'commentary', label: 'Commentary', icon: MessageSquare },
  { key: 'events', label: 'Events', icon: List },
]

export default function MatchDetailPage({ params }: { params: { id: string } }) {
  const matchId = parseInt(params.id)
  const [activeTab, setActiveTab] = useState('stream')
  const [liveScore, setLiveScore] = useState<{ home?: number; away?: number } | null>(null)

  const { data: match, isLoading } = useQuery({
    queryKey: ['match', matchId],
    queryFn: () => matchApi.get(matchId),
    refetchInterval: (query) => query.state.data?.status === 'live' ? 30020 : false,
  })

  const { data: commentary } = useQuery({
    queryKey: ['match-commentary', matchId],
    queryFn: () => matchApi.commentary(matchId),
    enabled: activeTab === 'commentary',
  })

  const { data: events } = useQuery({
    queryKey: ['match-events', matchId],
    queryFn: () => matchApi.events(matchId),
    enabled: activeTab === 'events',
  })

  // WebSocket for real-time score
  useEffect(() => {
    if (!match) return
    const ws = createMatchWS(matchId)

    ws.on('score_update', (data: unknown) => {
      const d = data as { score?: { home?: number; away?: number } }
      if (d.score) setLiveScore(d.score)
    })

    ws.on('match_data', (data: unknown) => {
      const d = data as { score_summary?: { home?: number; away?: number } }
      if (d.score_summary) setLiveScore(d.score_summary)
    })

    ws.connect()
    return () => ws.disconnect()
  }, [matchId, match])

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-zinc-800 rounded w-64" />
          <div className="aspect-video bg-zinc-900 rounded-xl" />
        </div>
      </div>
    )
  }

  if (!match) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center text-zinc-500">
        Match not found
      </div>
    )
  }

  const score = liveScore || match.score_summary
  const isLive = match.status === 'live'

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Match header */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 mb-6">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="text-sm text-zinc-500">{match.league.name}</span>
            {isLive && (
              <span className="live-badge">LIVE</span>
            )}
          </div>

          <div className="flex items-center justify-center gap-8">
            {/* Home team */}
            <div className="flex flex-col items-center gap-2 flex-1">
              <div className="text-xl font-bold text-zinc-100">{match.home_team.name}</div>
              <div className="text-sm text-zinc-400">{match.home_team.short_name}</div>
            </div>

            {/* Score */}
            <div className="flex flex-col items-center gap-1">
              {score?.home !== undefined ? (
                <div className={`text-4xl font-bold ${isLive ? 'text-red-400' : 'text-zinc-100'}`}>
                  {score.home} — {score.away}
                </div>
              ) : (
                <div className="text-2xl text-zinc-400">
                  {format(new Date(match.start_time), 'HH:mm')}
                </div>
              )}
              <div className="text-sm text-zinc-500 capitalize">{match.status}</div>
            </div>

            {/* Away team */}
            <div className="flex flex-col items-center gap-2 flex-1">
              <div className="text-xl font-bold text-zinc-100">{match.away_team.name}</div>
              <div className="text-sm text-zinc-400">{match.away_team.short_name}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Tabs */}
          <div className="flex gap-1 bg-zinc-900 p-1 rounded-xl w-fit">
            {DETAIL_TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === key ? 'bg-red-600 text-white' : 'text-zinc-400 hover:text-zinc-100'
                }`}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'stream' && (
            <VideoPlayer streams={match.stream_sources} />
          )}

          {activeTab === 'commentary' && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <h3 className="font-semibold mb-4">Live Commentary</h3>
              <CommentaryFeed matchId={matchId} initialCommentary={commentary} />
            </div>
          )}

          {activeTab === 'events' && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <h3 className="font-semibold mb-4">Match Events</h3>
              <EventsList events={events || []} />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <h3 className="font-semibold mb-3 text-sm">Match Info</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-zinc-500">Sport</dt>
                <dd className="text-zinc-100">{match.league.sport?.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">League</dt>
                <dd className="text-zinc-100">{match.league.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">Date</dt>
                <dd className="text-zinc-100">{format(new Date(match.start_time), 'MMM d, yyyy')}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">Time</dt>
                <dd className="text-zinc-100">{format(new Date(match.start_time), "HH:mm 'UTC'")}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-zinc-500">Streams</dt>
                <dd className="text-zinc-100">{match.stream_sources.length}</dd>
              </div>
            </dl>
          </div>

          {typeof match.metadata?.ai_summary === 'string' && match.metadata.ai_summary && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <h3 className="font-semibold mb-3 text-sm flex items-center gap-2">
                AI Summary
              </h3>
              <p className="text-sm text-zinc-300 leading-relaxed">
                {match.metadata.ai_summary}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function EventsList({ events }: { events: ScoreEvent[] }) {
  const eventIcons: Record<string, string> = {
    goal: '⚽', wicket: '🏏', boundary: '4️⃣', six: '6️⃣',
    yellow_card: '🟨', red_card: '🟥', substitution: '🔄',
    penalty: '🎯', var_check: '📺', period_start: '▶️', period_end: '⏹️',
  }

  if (!events.length) {
    return <p className="text-zinc-500 text-sm">No events yet.</p>
  }

  return (
    <div className="space-y-2">
      {events.map(event => (
        <div key={event.id} className="flex items-center gap-3 py-2 border-b border-zinc-800 last:border-0">
          <span className="text-lg">{eventIcons[event.event_type] || '•'}</span>
          <div className="flex-1">
            <span className="text-sm text-zinc-200 font-medium">{event.player_name || event.event_type}</span>
            {event.minute && (
              <span className="ml-2 text-xs text-zinc-500">{event.minute}&apos;</span>
            )}
          </div>
          <span className="text-xs text-zinc-500 capitalize">{event.team_side}</span>
        </div>
      ))}
    </div>
  )
}
