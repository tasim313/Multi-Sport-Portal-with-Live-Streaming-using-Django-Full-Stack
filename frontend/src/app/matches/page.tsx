'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { matchApi } from '@/lib/api'
import { MatchCard } from '@/components/match/MatchCard'
import { SkeletonCard } from '@/components/ui/SkeletonCard'

const TABS = [
  { key: 'live', label: 'Live' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'finished', label: 'Results' },
]

export default function MatchesPage() {
  const [activeTab, setActiveTab] = useState('live')
  const [sport, setSport] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['matches', activeTab, sport],
    queryFn: () => matchApi.list({
      status: activeTab,
      ...(sport ? { sport } : {}),
    }),
    refetchInterval: activeTab === 'live' ? 15000 : false,
  })

  const matches = data?.results || []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <h1 className="text-2xl font-bold mb-6">Matches</h1>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-zinc-900 p-1 rounded-xl w-fit">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab.key
                ? 'bg-red-600 text-white'
                : 'text-zinc-400 hover:text-zinc-100'
            }`}
          >
            {tab.label}
            {tab.key === 'live' && data && matches.length > 0 && (
              <span className="ml-1.5 bg-red-700 text-white text-xs px-1.5 py-0.5 rounded-full">
                {matches.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Results grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : matches.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {matches.map(match => (
            <MatchCard key={match.id} match={match} />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 text-zinc-500">
          <p className="text-lg">No {activeTab} matches right now</p>
          <p className="text-sm mt-1">Check back later or browse other tabs</p>
        </div>
      )}
    </div>
  )
}
