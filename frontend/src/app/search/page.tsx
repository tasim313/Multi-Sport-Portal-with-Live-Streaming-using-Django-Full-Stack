'use client'

import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { searchApi } from '@/lib/api'
import { MatchCard } from '@/components/match/MatchCard'
import { ChannelCard } from '@/components/iptv/ChannelCard'
import Link from 'next/link'
import { format } from 'date-fns'
import { Suspense } from 'react'

function SearchResults() {
  const searchParams = useSearchParams()
  const q = searchParams.get('q') || ''

  const { data, isLoading } = useQuery({
    queryKey: ['search', q],
    queryFn: () => searchApi.search(q),
    enabled: q.length >= 2,
  })

  if (q.length < 2) {
    return <p className="text-zinc-500 text-center py-20">Enter at least 2 characters to search.</p>
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const total = (data?.matches?.length || 0) + (data?.articles?.length || 0) +
    (data?.teams?.length || 0) + (data?.channels?.length || 0)

  return (
    <div className="space-y-8">
      <p className="text-zinc-500 text-sm">{total} results for &quot;{q}&quot;</p>

      {data?.matches && data.matches.length > 0 && (
        <section>
          <h2 className="section-title mb-4">Matches</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.matches.map(m => <MatchCard key={m.id} match={m} />)}
          </div>
        </section>
      )}

      {data?.channels && data.channels.length > 0 && (
        <section>
          <h2 className="section-title mb-4">IPTV Channels</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {data.channels.map(c => <ChannelCard key={c.id} channel={c} />)}
          </div>
        </section>
      )}

      {data?.articles && data.articles.length > 0 && (
        <section>
          <h2 className="section-title mb-4">News</h2>
          <div className="space-y-2">
            {data.articles.map(a => (
              <Link key={a.id} href={`/news/${a.slug}`} className="flex gap-4 p-3 bg-zinc-900 rounded-xl hover:border-zinc-600 border border-zinc-800 transition-colors">
                <div>
                  <div className="text-xs text-red-400 font-medium mb-1">{a.category}</div>
                  <div className="font-medium text-zinc-100 text-sm">{a.title}</div>
                  <div className="text-xs text-zinc-500 mt-1">{format(new Date(a.published_at), 'MMM d, yyyy')}</div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {data?.teams && data.teams.length > 0 && (
        <section>
          <h2 className="section-title mb-4">Teams</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {data.teams.map(t => (
              <div key={t.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 text-sm">
                <div className="font-medium text-zinc-100">{t.name}</div>
                <div className="text-xs text-zinc-500">{t.league?.name}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {total === 0 && (
        <p className="text-center py-20 text-zinc-500">No results found for &quot;{q}&quot;</p>
      )}
    </div>
  )
}

export default function SearchPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <h1 className="text-2xl font-bold mb-6">Search Results</h1>
      <Suspense fallback={
        <div className="flex items-center justify-center py-20">
          <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }>
        <SearchResults />
      </Suspense>
    </div>
  )
}
