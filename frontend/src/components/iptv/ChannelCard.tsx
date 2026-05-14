import Link from 'next/link'
import Image from 'next/image'
import { Tv } from 'lucide-react'
import type { IPTVChannel } from '@/types'

interface ChannelCardProps {
  channel: IPTVChannel
}

export function ChannelCard({ channel }: ChannelCardProps) {
  return (
    <Link href={`/iptv/${channel.slug}`}>
      <div className="channel-card group">
        {/* Logo */}
        <div className="flex items-center justify-center h-14">
          {channel.logo ? (
            <Image
              src={channel.logo}
              alt={channel.name}
              width={56}
              height={56}
              className="object-contain h-12 w-auto"
              unoptimized
            />
          ) : (
            <div className="w-12 h-12 bg-zinc-800 rounded-lg flex items-center justify-center">
              <Tv size={20} className="text-zinc-500" />
            </div>
          )}
        </div>

        {/* Name */}
        <p className="text-xs font-semibold text-zinc-200 text-center truncate group-hover:text-white transition-colors">
          {channel.name}
        </p>

        {/* Current program */}
        {channel.current_program && (
          <p className="text-[10px] text-zinc-500 text-center truncate">
            {channel.current_program.title}
          </p>
        )}

        {/* Country / Language */}
        <div className="flex items-center justify-center gap-1">
          {channel.country_code && (
            <span className="text-[10px] bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-400 uppercase">
              {channel.country_code}
            </span>
          )}
          {!channel.is_working && (
            <span className="text-[10px] bg-red-900/30 px-1.5 py-0.5 rounded text-red-400">
              Offline
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
