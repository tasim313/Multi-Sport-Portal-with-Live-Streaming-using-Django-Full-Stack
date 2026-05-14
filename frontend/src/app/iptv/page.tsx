'use client'

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { iptvApi } from '@/lib/api'
import { ChannelCard } from '@/components/iptv/ChannelCard'
import { SkeletonChannelCard } from '@/components/ui/SkeletonCard'
import { Search } from 'lucide-react'

const CATEGORIES = ['All', 'Sports', 'News', 'Entertainment', 'Movies', 'Kids', 'Music']

export default function IPTVPage() {
  const [category, setCategory] = useState('')
  const [searchQ, setSearchQ] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')

  const debounce = useCallback((fn: () => void, delay: number) => {
    let timer: ReturnType<typeof setTimeout>
    return () => {
      clearTimeout(timer)
      timer = setTimeout(fn, delay)
    }
  }, [])

  const handleSearch = (q: string) => {
    setSearchQ(q)
    const debounced = debounce(() => setDebouncedQ(q), 300)
    debounced()
  }

  const params: Record<string, string> = {
    page_size: '48',
    working: '1',
  }
  if (category) params.category = category
  if (debouncedQ) params.q = debouncedQ

  const { data, isLoading } = useQuery({
    queryKey: ['iptv-channels', category, debouncedQ],
    queryFn: () => iptvApi.list(params),
  })

  const channels = data?.results || []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1">Live TV — IPTV Channels</h1>
        <p className="text-zinc-500 text-sm">
          Stream thousands of live TV channels from around the world.
        </p>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <input
          type="text"
          value={searchQ}
          onChange={e => handleSearch(e.target.value)}
          placeholder="Search channels..."
          className="w-full sm:w-80 pl-9 pr-4 py-2.5 bg-zinc-900 border border-zinc-700 rounded-xl text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500"
        />
      </div>

      {/* Category tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            onClick={() => setCategory(cat === 'All' ? '' : cat)}
            className={`flex-shrink-0 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              (cat === 'All' && !category) || cat === category
                ? 'bg-red-600 text-white'
                : 'bg-zinc-900 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Channels grid */}
      {isLoading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
          {Array.from({ length: 24 }).map((_, i) => <SkeletonChannelCard key={i} />)}
        </div>
      ) : channels.length > 0 ? (
        <>
          <p className="text-xs text-zinc-600 mb-3">{data?.count?.toLocaleString()} channels found</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
            {channels.map(channel => (
              <ChannelCard key={channel.id} channel={channel} />
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-20 text-zinc-500">
          <p>No channels found{category ? ` for "${category}"` : ''}.</p>
        </div>
      )}
    </div>
  )
}
