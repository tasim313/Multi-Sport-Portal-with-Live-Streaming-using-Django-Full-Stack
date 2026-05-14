import { articleApi } from '@/lib/api'
import Link from 'next/link'
import Image from 'next/image'
import { format } from 'date-fns'

const CATEGORIES = [
  { key: '', label: 'All' },
  { key: 'news', label: 'News' },
  { key: 'preview', label: 'Previews' },
  { key: 'review', label: 'Reviews' },
  { key: 'highlight', label: 'Highlights' },
  { key: 'transfer', label: 'Transfers' },
]

async function getArticles(category?: string) {
  try {
    return await articleApi.list({
      page_size: '20',
      ...(category ? { category } : {}),
    })
  } catch {
    return { results: [], count: 0, next: null, previous: null }
  }
}

export default async function NewsPage({
  searchParams,
}: {
  searchParams: { category?: string }
}) {
  const category = searchParams.category || ''
  const data = await getArticles(category)
  const articles = data.results

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <h1 className="text-2xl font-bold mb-6">Sports News</h1>

      {/* Category filter */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {CATEGORIES.map(cat => (
          <Link
            key={cat.key}
            href={cat.key ? `/news?category=${cat.key}` : '/news'}
            className={`flex-shrink-0 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              cat.key === category
                ? 'bg-red-600 text-white'
                : 'bg-zinc-900 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800'
            }`}
          >
            {cat.label}
          </Link>
        ))}
      </div>

      {articles.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map(article => (
            <Link key={article.id} href={`/news/${article.slug}`}>
              <div className="news-card group h-full">
                {article.hero_image && (
                  <div className="relative h-48 overflow-hidden">
                    <Image
                      src={article.hero_image}
                      alt={article.title}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-300"
                      unoptimized
                    />
                  </div>
                )}
                <div className="p-5 flex flex-col flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] uppercase tracking-wider text-red-400 font-bold">
                      {article.category}
                    </span>
                    <span className="text-[10px] text-zinc-600">
                      {format(new Date(article.published_at), 'MMM d, yyyy')}
                    </span>
                  </div>
                  <h2 className="font-bold text-zinc-100 text-base leading-snug mb-2 group-hover:text-white line-clamp-3">
                    {article.title}
                  </h2>
                  {article.excerpt && (
                    <p className="text-sm text-zinc-500 line-clamp-2 flex-1">{article.excerpt}</p>
                  )}
                  <div className="mt-3 flex items-center gap-2 text-xs text-zinc-600">
                    <span>{article.author}</span>
                    <span>·</span>
                    <span>{article.views_count} views</span>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 text-zinc-500">
          No articles found.
        </div>
      )}
    </div>
  )
}
