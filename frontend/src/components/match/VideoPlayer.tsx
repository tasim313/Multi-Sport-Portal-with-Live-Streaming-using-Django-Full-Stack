'use client'

import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import { AlertCircle, RefreshCw } from 'lucide-react'
import type { StreamSource } from '@/types'

interface VideoPlayerProps {
  streams: StreamSource[]
  autoPlay?: boolean
}

export function VideoPlayer({ streams, autoPlay = true }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const [currentStreamIdx, setCurrentStreamIdx] = useState(0)
  const [error, setError] = useState(false)
  const [loading, setLoading] = useState(true)

  const activeStreams = streams.filter(s => s.is_active)
  const current = activeStreams[currentStreamIdx]

  useEffect(() => {
    if (!current || !videoRef.current) return

    setError(false)
    setLoading(true)

    // If stream has embed HTML (YouTube/Vimeo iframe), skip video element
    if (current.is_iframe && current.embed_html) {
      setLoading(false)
      return
    }

    const video = videoRef.current

    // Destroy previous HLS instance
    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }

    const url = current.url

    if (url.includes('.m3u8') || url.includes('m3u')) {
      if (Hls.isSupported()) {
        const hls = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 30,
        })
        hlsRef.current = hls

        hls.loadSource(url)
        hls.attachMedia(video)

        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          setLoading(false)
          if (autoPlay) video.play().catch(() => {})
        })

        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) {
            setError(true)
            setLoading(false)
            // Auto-switch to next stream
            if (currentStreamIdx < activeStreams.length - 1) {
              setTimeout(() => setCurrentStreamIdx(idx => idx + 1), 2000)
            }
          }
        })
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Safari native HLS
        video.src = url
        video.addEventListener('loadedmetadata', () => {
          setLoading(false)
          if (autoPlay) video.play().catch(() => {})
        })
      }
    } else {
      // Direct video URL
      video.src = url
      video.addEventListener('loadedmetadata', () => setLoading(false))
      video.addEventListener('error', () => {
        setError(true)
        setLoading(false)
      })
      if (autoPlay) video.play().catch(() => {})
    }

    return () => {
      hlsRef.current?.destroy()
    }
  }, [current, currentStreamIdx, activeStreams.length, autoPlay])

  if (!activeStreams.length) {
    return (
      <div className="aspect-video bg-zinc-900 rounded-xl flex items-center justify-center">
        <div className="text-center text-zinc-500">
          <AlertCircle className="mx-auto mb-2" size={32} />
          <p>No streams available</p>
        </div>
      </div>
    )
  }

  // Iframe stream (YouTube/Vimeo)
  if (current?.is_iframe && current.embed_html) {
    return (
      <div className="relative">
        <div
          className="aspect-video bg-black rounded-xl overflow-hidden"
          dangerouslySetInnerHTML={{ __html: current.embed_html }}
        />
        <StreamSwitcher
          streams={activeStreams}
          current={currentStreamIdx}
          onChange={setCurrentStreamIdx}
        />
      </div>
    )
  }

  return (
    <div className="relative group">
      <div className="aspect-video bg-black rounded-xl overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-zinc-400 text-sm">Loading stream...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-black">
            <div className="text-center">
              <AlertCircle className="mx-auto mb-2 text-red-400" size={32} />
              <p className="text-zinc-400 text-sm mb-3">Stream unavailable</p>
              {currentStreamIdx < activeStreams.length - 1 && (
                <button
                  onClick={() => setCurrentStreamIdx(idx => idx + 1)}
                  className="btn-secondary text-sm flex items-center gap-2 mx-auto"
                >
                  <RefreshCw size={14} />
                  Try next stream
                </button>
              )}
            </div>
          </div>
        )}

        <video
          ref={videoRef}
          className="w-full h-full"
          controls
          playsInline
          muted
        />
      </div>

      <StreamSwitcher
        streams={activeStreams}
        current={currentStreamIdx}
        onChange={setCurrentStreamIdx}
      />
    </div>
  )
}

function StreamSwitcher({
  streams,
  current,
  onChange,
}: {
  streams: StreamSource[]
  current: number
  onChange: (idx: number) => void
}) {
  if (streams.length <= 1) return null

  return (
    <div className="flex items-center gap-2 mt-2 flex-wrap">
      <span className="text-xs text-zinc-500">Streams:</span>
      {streams.map((s, i) => (
        <button
          key={s.id}
          onClick={() => onChange(i)}
          className={`text-xs px-2 py-1 rounded font-medium transition-colors ${
            i === current
              ? 'bg-red-600 text-white'
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
          }`}
        >
          {s.provider} #{i + 1}
        </button>
      ))}
    </div>
  )
}
