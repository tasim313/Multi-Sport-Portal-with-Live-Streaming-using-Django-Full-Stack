import { articleApi } from '@/lib/api'
import Image from 'next/image'
import Link from 'next/link'
import { format } from 'date-fns'
import { ArrowLeft } from 'lucide-react'
import type { Metadata } from 'next'

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  try {
    const article = await articleApi.get(params.slug)
    return {
      title: article.title,
      description: article.meta_description || article.excerpt,
    }
  } catch {
    return { title: 'Article' }
  }
}

export default async function ArticlePage({ params }: { params: { slug: string } }) {
  let article
  try {
    article = await articleApi.get(params.slug)
  } catch {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center text-zinc-500">
        Article not found.
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      {/* Back */}
      <Link href="/news" className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 mb-6 transition-colors">
        <ArrowLeft size={14} />
        Back to News
      </Link>

      {/* Hero image */}
      {article.hero_image && (
        <div className="relative h-64 md:h-96 rounded-xl overflow-hidden mb-8">
          <Image src={article.hero_image} alt={article.title} fill className="object-cover" unoptimized />
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-xs uppercase tracking-wider text-red-400 font-bold">{article.category}</span>
          {article.sport && (
            <span className="text-xs text-zinc-600">· {article.sport.name}</span>
          )}
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-zinc-100 mb-4 leading-tight">
          {article.title}
        </h1>

        <div className="flex items-center gap-3 text-sm text-zinc-500">
          {article.author && <span>By {article.author}</span>}
          <span>·</span>
          <time>{format(new Date(article.published_at), 'MMMM d, yyyy')}</time>
          <span>·</span>
          <span>{article.views_count} views</span>
        </div>

        {article.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {article.tags.map((tag: string) => (
              <span key={tag} className="text-[11px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="prose prose-invert prose-zinc max-w-none text-zinc-300 text-base leading-relaxed">
        {article.body.split('\n').filter(Boolean).map((para, i) => (
          <p key={i} className="mb-4">{para}</p>
        ))}
      </div>
    </div>
  )
}
