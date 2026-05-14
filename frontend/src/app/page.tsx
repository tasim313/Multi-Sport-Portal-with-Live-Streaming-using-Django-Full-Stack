import { matchApi, articleApi, iptvApi } from '@/lib/api'
import { MatchCard } from '@/components/match/MatchCard'
import { ChannelCard } from '@/components/iptv/ChannelCard'
import Link from 'next/link'
import Image from 'next/image'
import { format } from 'date-fns'
import { ArrowRight, Play } from 'lucide-react'

async function getData() {
  try {
    const [liveMatches, upcomingMatches, articles, channels] = await Promise.allSettled([
      matchApi.live(),
      matchApi.upcoming(),
      articleApi.list({ page_size: '6' }),
      iptvApi.list({ category: 'Sports', page_size: '8', working: '1' }),
    ])

    return {
      liveMatches: liveMatches.status === 'fulfilled' ? liveMatches.value : [],
      upcomingMatches: upcomingMatches.status === 'fulfilled' ? upcomingMatches.value : [],
      articles: articles.status === 'fulfilled' ? articles.value.results : [],
      channels: channels.status === 'fulfilled' ? channels.value.results : [],
    }
  } catch {
    return { liveMatches: [], upcomingMatches: [], articles: [], channels: [] }
  }
}

export default async function HomePage() {
  const { liveMatches, upcomingMatches, articles, channels } = await getData()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-10">

      {/* Hero banner */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-zinc-900 via-zinc-900 to-red-950 border border-zinc-800 p-8 md:p-12">
        <div className="relative z-10">
          <h1 className="text-3xl md:text-5xl font-bold text-white mb-3">
            Live Sports & <span className="text-red-500">IPTV</span> Streaming
          </h1>
          <p className="text-zinc-400 text-lg mb-6 max-w-lg">
            Watch live matches, 10,000+ IPTV channels, real-time scores, and AI-powered commentary.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/matches?status=live" className="btn-primary flex items-center gap-2">
              <Play size={16} />
              Watch Live
            </Link>
            <Link href="/iptv" className="btn-secondary flex items-center gap-2">
              Browse IPTV
            </Link>
          </div>
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-64 opacity-5 bg-gradient-to-l from-red-500" />
      </section>

      {/* Live Matches */}
      {liveMatches.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">
              <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse-fast" />
              Live Now
            </h2>
            <Link href="/matches?status=live" className="text-sm text-red-400 hover:text-red-300 flex items-center gap-1">
              All live <ArrowRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {liveMatches.map(match => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        </section>
      )}

      {/* Upcoming Matches */}
      {upcomingMatches.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Upcoming Matches</h2>
            <Link href="/matches" className="text-sm text-zinc-400 hover:text-zinc-100 flex items-center gap-1">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {upcomingMatches.slice(0, 6).map(match => (
              <MatchCard key={match.id} match={match} />
            ))}
          </div>
        </section>
      )}

      {/* Sports TV Channels */}
      {channels.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Sports TV Channels</h2>
            <Link href="/iptv?category=Sports" className="text-sm text-zinc-400 hover:text-zinc-100 flex items-center gap-1">
              All channels <ArrowRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-3">
            {channels.map(channel => (
              <ChannelCard key={channel.id} channel={channel} />
            ))}
          </div>
        </section>
      )}

      {/* Latest News */}
      {articles.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Latest News</h2>
            <Link href="/news" className="text-sm text-zinc-400 hover:text-zinc-100 flex items-center gap-1">
              All news <ArrowRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {articles.map(article => (
              <Link key={article.id} href={`/news/${article.slug}`}>
                <div className="news-card group">
                  {article.hero_image && (
                    <div className="relative h-40 overflow-hidden">
                      <Image
                        src={article.hero_image}
                        alt={article.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-300"
                        unoptimized
                      />
                    </div>
                  )}
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] uppercase tracking-wide text-red-400 font-bold">
                        {article.category}
                      </span>
                      <span className="text-[10px] text-zinc-600">
                        {format(new Date(article.published_at), 'MMM d, yyyy')}
                      </span>
                    </div>
                    <h3 className="font-semibold text-zinc-100 text-sm leading-tight line-clamp-2 group-hover:text-white">
                      {article.title}
                    </h3>
                    {article.excerpt && (
                      <p className="mt-1 text-xs text-zinc-500 line-clamp-2">{article.excerpt}</p>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
