import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { Navbar } from '@/components/layout/Navbar'
import { LiveScoreTicker } from '@/components/layout/LiveScoreTicker'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: {
    default: 'SportPortal — Live Sports Streaming & IPTV',
    template: '%s | SportPortal',
  },
  description: 'Watch live sports, IPTV channels, live scores and sports news. Football, Cricket, Tennis, Basketball and more.',
  keywords: ['live sports', 'IPTV', 'live streaming', 'cricket', 'football', 'tennis', 'basketball', 'live scores'],
  openGraph: {
    type: 'website',
    title: 'SportPortal — Live Sports Streaming & IPTV',
    description: 'Watch live sports, IPTV channels, live scores and sports news.',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <Providers>
          <Navbar />
          <LiveScoreTicker />
          <main className="pt-0">
            {children}
          </main>
          <Toaster
            position="bottom-right"
            toastOptions={{
              style: {
                background: '#18181b',
                color: '#f4f4f5',
                border: '1px solid #3f3f46',
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
