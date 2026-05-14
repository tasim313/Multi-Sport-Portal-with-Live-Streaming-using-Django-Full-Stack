'use client'

import { useQuery } from '@tanstack/react-query'
import { iptvApi } from '@/lib/api'
import { VideoPlayer } from '@/components/match/VideoPlayer'
import { format } from 'date-fns'
import Image from 'next/image'
import { Tv, Globe, Info } from 'lucide-react'

export default function ChannelDetailPage({ params }: { params: { slug: string } }) {
  const { data: channel, isLoading } = useQuery({
    queryKey: ['iptv-channel', params.slug],
    queryFn: () => iptvApi.get(params.slug),
  })

  const { data: epg } = useQuery({
    queryKey: ['iptv-epg', params.slug],
    queryFn: () => iptvApi.epg(params.slug),
    enabled: !!channel,
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-6 animate-pulse">
        <div className="aspect-video bg-zinc-900 rounded-xl mb-4" />
        <div className="h-6 bg-zinc-800 rounded w-48" />
      </div>
    )
  }

  if (!channel) {
    return <div className="text-center py-20 text-zinc-500">Channel not found</div>
  }

  // Build stream source for VideoPlayer
  const streamSource = [{
    id: channel.id,
    provider: 'hls' as const,
    url: channel.stream_url,
    embed_html: '',
    is_iframe: false,
    requires_auth: false,
    priority: 1,
    is_active: channel.is_working,
  }]

  const now = new Date()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Player */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center gap-3 mb-2">
            {channel.logo ? (
              <Image src={channel.logo} alt={channel.name} width={40} height={40} className="object-contain" unoptimized />
            ) : (
              <div className="w-10 h-10 bg-zinc-800 rounded-lg flex items-center justify-center">
                <Tv size={18} className="text-zinc-500" />
              </div>
            )}
            <div>
              <h1 className="text-xl font-bold">{channel.name}</h1>
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <Globe size={11} />
                {channel.country || 'International'} · {channel.category}
                {!channel.is_working && (
                  <span className="text-red-400 ml-1">· Offline</span>
                )}
              </div>
            </div>
          </div>

          {channel.current_program && (
            <div className="flex items-center gap-2 px-3 py-2 bg-zinc-900 rounded-lg border border-zinc-800">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse-fast flex-shrink-0" />
              <span className="text-sm text-zinc-200 font-medium">
                Now Playing: {channel.current_program.title}
              </span>
              <span className="text-xs text-zinc-500 ml-auto">
                Until {format(new Date(channel.current_program.end_time), 'HH:mm')}
              </span>
            </div>
          )}

          <VideoPlayer streams={streamSource} />

          <div className="flex items-start gap-2 p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-xs text-zinc-500">
            <Info size={12} className="flex-shrink-0 mt-0.5" />
            <span>{channel.attribution}</span>
          </div>
        </div>

        {/* EPG sidebar */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <h3 className="font-semibold mb-4 text-sm">Program Guide</h3>
          {epg && epg.length > 0 ? (
            <div className="space-y-2">
              {epg.map(program => {
                const isNow = program.is_live
                return (
                  <div
                    key={program.id}
                    className={`p-2.5 rounded-lg ${isNow ? 'bg-red-950/40 border border-red-900/50' : 'bg-zinc-800/50'}`}
                  >
                    <div className="flex items-center gap-1.5 mb-0.5">
                      {isNow && <span className="w-1.5 h-1.5 bg-red-500 rounded-full" />}
                      <span className="text-xs font-medium text-zinc-200 truncate">
                        {program.title}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-500">
                      {format(new Date(program.start_time), 'HH:mm')} — {format(new Date(program.end_time), 'HH:mm')}
                    </span>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-xs text-zinc-500">No EPG data available for this channel.</p>
          )}

          {/* Channel info */}
          <div className="mt-6 pt-4 border-t border-zinc-800 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-zinc-500">Language</span>
              <span className="text-zinc-300">{channel.language || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Country</span>
              <span className="text-zinc-300">{channel.country || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Category</span>
              <span className="text-zinc-300">{channel.category || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-zinc-500">Source</span>
              <span className="text-zinc-300">{channel.source_name}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
