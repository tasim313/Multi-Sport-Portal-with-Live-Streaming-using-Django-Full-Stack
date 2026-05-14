export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-zinc-900 border border-zinc-800 rounded-xl p-4 ${className}`}>
      <div className="space-y-3">
        <div className="skeleton h-4 w-20 rounded" />
        <div className="flex items-center justify-between">
          <div className="skeleton h-8 w-24 rounded" />
          <div className="skeleton h-10 w-16 rounded" />
          <div className="skeleton h-8 w-24 rounded" />
        </div>
        <div className="skeleton h-3 w-32 rounded" />
      </div>
    </div>
  )
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={`skeleton h-4 rounded ${i === lines - 1 ? 'w-2/3' : 'w-full'}`}
        />
      ))}
    </div>
  )
}

export function SkeletonChannelCard() {
  return (
    <div className="channel-card">
      <div className="skeleton h-12 w-12 rounded-lg mx-auto" />
      <div className="skeleton h-4 w-24 rounded mx-auto" />
      <div className="skeleton h-3 w-16 rounded mx-auto" />
    </div>
  )
}
