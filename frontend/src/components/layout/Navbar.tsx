'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useAuthStore } from '@/store/auth'
import { Menu, X, Search, User, Tv, Trophy, Newspaper, Home, LogOut } from 'lucide-react'

export function Navbar() {
  const [open, setOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQ, setSearchQ] = useState('')
  const { isLoggedIn, user, logout } = useAuthStore()

  const navLinks = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/matches', label: 'Matches', icon: Trophy },
    { href: '/iptv', label: 'Live TV', icon: Tv },
    { href: '/news', label: 'News', icon: Newspaper },
  ]

  return (
    <nav className="sticky top-0 z-50 bg-zinc-950/95 backdrop-blur-sm border-b border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl">
            <span className="text-red-500">Sport</span>
            <span className="text-zinc-100">Portal</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <Icon size={15} />
                {label}
              </Link>
            ))}
          </div>

          {/* Right section */}
          <div className="flex items-center gap-2">
            {/* Search */}
            <div className="relative">
              {searchOpen ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={searchQ}
                    onChange={(e) => setSearchQ(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && searchQ.trim()) {
                        window.location.href = `/search?q=${encodeURIComponent(searchQ)}`
                      }
                      if (e.key === 'Escape') setSearchOpen(false)
                    }}
                    placeholder="Search..."
                    autoFocus
                    className="w-48 px-3 py-1.5 text-sm bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500"
                  />
                  <button onClick={() => setSearchOpen(false)} className="text-zinc-400 hover:text-zinc-100">
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setSearchOpen(true)}
                  className="p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
                >
                  <Search size={18} />
                </button>
              )}
            </div>

            {/* Auth */}
            {isLoggedIn ? (
              <div className="flex items-center gap-2">
                <Link
                  href="/profile"
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-zinc-300 hover:text-zinc-100 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                  <User size={15} />
                  {user?.username || 'Profile'}
                </Link>
                <button
                  onClick={logout}
                  className="p-2 text-zinc-400 hover:text-red-400 transition-colors"
                  title="Sign out"
                >
                  <LogOut size={16} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link href="/login" className="px-3 py-1.5 text-sm font-medium text-zinc-300 hover:text-zinc-100 transition-colors">
                  Sign In
                </Link>
                <Link href="/register" className="btn-primary text-sm py-1.5">
                  Register
                </Link>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button
              className="md:hidden p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg"
              onClick={() => setOpen(!open)}
            >
              {open ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-zinc-800 bg-zinc-950">
          <div className="px-4 py-3 space-y-1">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-zinc-300 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  )
}
