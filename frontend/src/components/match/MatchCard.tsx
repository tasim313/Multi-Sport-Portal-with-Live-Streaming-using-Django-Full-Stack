import Link from 'next/link'
import Image from 'next/image'
import { format } from 'date-fns'
import type { Match } from '@/types'

interface MatchCardProps {
  match: Match
}

const statusConfig = {
  live: { label: 'LIVE', class: 'live-badge' },
  scheduled: { label: 'UPCOMING', class: 'bg-zinc-700 text-zinc-300 text-xs px-2 py-0.5 rounded font-medium' },
  finished: { label: 'FT', class: 'bg-zinc-800 text-zinc-400 text-xs px-2 py-0.5 rounded font-medium' },
  postponed: { label: 'PPD', class: 'bg-amber-900/50 text-amber-400 text-xs px-2 py-0.5 rounded font-medium' },
  cancelled: { label: 'CAN', class: 'bg-red-900/30 text-red-400 text-xs px-2 py-0.5 rounded font-medium' },
}

export function MatchCard({ match }: MatchCardProps) {
  const status = statusConfig[match.status] || statusConfig.scheduled
  const homeScore = match.score_summary?.home ?? null
  const awayScore = match.score_summary?.away ?? null
  const isLive = match.status === 'live'

  return (
    <Link href={`/matches/${match.id}`}>
      <div className="match-card group">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            {match.league.logo && (
              <Image
                src={match.league.logo}
                alt={match.league.name}
                width={16}
                height={16}
                className="rounded-sm object-contain"
                unoptimized
              />
            )}
            <span className="text-xs text-zinc-500 font-medium truncate max-w-[140px]">
              {match.league.name}
            </span>
          </div>
          <span className={status.class}>{status.label}</span>
        </div>

        {/* Teams & Score */}
        <div className="flex items-center justify-between gap-3">
          {/* Home team */}
          <div className="flex-1 flex flex-col items-center gap-1">
            {match.home_team.logo && (
              <Image
                src={match.home_team.logo}
                alt={match.home_team.name}
                width={36}
                height={36}
                className="object-contain"
                unoptimized
              />
            )}
            <span className="text-sm font-semibold text-zinc-100 text-center leading-tight">
              {match.home_team.name}
            </span>
          </div>

          {/* Score */}
          <div className="flex flex-col items-center gap-1">
            {homeScore !== null ? (
              <div className={`text-2xl font-bold ${isLive ? 'text-red-400' : 'text-zinc-100'}`}>
                {homeScore} — {awayScore}
              </div>
            ) : (
              <div className="text-sm text-zinc-500 font-medium">
                {format(new Date(match.start_time), 'HH:mm')}
              </div>
            )}
            {isLive && (
              <div className="text-xs text-red-400 font-medium">In Progress</div>
            )}
            {match.status === 'scheduled' && (
              <div className="text-[10px] text-zinc-600">
                {format(new Date(match.start_time), 'MMM d')}
              </div>
            )}
          </div>

          {/* Away team */}
          <div className="flex-1 flex flex-col items-center gap-1">
            {match.away_team.logo && (
              <Image
                src={match.away_team.logo}
                alt={match.away_team.name}
                width={36}
                height={36}
                className="object-contain"
                unoptimized
              />
            )}
            <span className="text-sm font-semibold text-zinc-100 text-center leading-tight">
              {match.away_team.name}
            </span>
          </div>
        </div>

        {/* Stream indicator */}
        {match.stream_sources.length > 0 && (
          <div className="mt-3 flex items-center justify-center gap-1 text-xs text-emerald-400">
            <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
            {match.stream_sources.length} stream{match.stream_sources.length > 1 ? 's' : ''} available
          </div>
        )}
      </div>
    </Link>
  )
}
