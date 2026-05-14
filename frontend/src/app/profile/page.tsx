'use client'

import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, favoritesApi } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'next/navigation'
import toast from 'react-hot-toast'
import { User, Star, Settings, LogOut } from 'lucide-react'

const TABS = [
  { key: 'profile', label: 'Profile', icon: User },
  { key: 'favorites', label: 'Favorites', icon: Star },
]

export default function ProfilePage() {
  const router = useRouter()
  const { isLoggedIn, logout } = useAuthStore()
  const [activeTab, setActiveTab] = useState('profile')
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!isLoggedIn) router.push('/login')
  }, [isLoggedIn, router])

  const { data: user, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: authApi.profile,
    enabled: isLoggedIn,
  })

  const { data: favorites } = useQuery({
    queryKey: ['favorites'],
    queryFn: favoritesApi.list,
    enabled: isLoggedIn && activeTab === 'favorites',
  })

  const updateMutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: () => {
      toast.success('Profile updated')
      queryClient.invalidateQueries({ queryKey: ['profile'] })
    },
    onError: () => toast.error('Update failed'),
  })

  const [bioInput, setBioInput] = useState('')
  useEffect(() => {
    if (user?.bio) setBioInput(user.bio)
  }, [user])

  if (!isLoggedIn || isLoading) {
    return <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
    </div>
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center">
            <User size={28} className="text-zinc-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{user?.username}</h1>
            <p className="text-zinc-500 text-sm">{user?.email}</p>
            <span className="text-xs bg-zinc-800 px-2 py-0.5 rounded text-zinc-400 mt-1 inline-block capitalize">
              {user?.role}
            </span>
          </div>
        </div>
        <button
          onClick={() => { logout(); router.push('/') }}
          className="flex items-center gap-2 text-sm text-zinc-400 hover:text-red-400 transition-colors"
        >
          <LogOut size={16} />
          Sign Out
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-zinc-900 p-1 rounded-xl w-fit">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === key ? 'bg-red-600 text-white' : 'text-zinc-400 hover:text-zinc-100'
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'profile' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 space-y-6">
          <div>
            <h3 className="text-sm font-semibold mb-4">Account Info</h3>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-zinc-500 mb-1">Username</dt>
                <dd className="text-zinc-100">{user?.username}</dd>
              </div>
              <div>
                <dt className="text-zinc-500 mb-1">Email</dt>
                <dd className="text-zinc-100">{user?.email}</dd>
              </div>
              <div>
                <dt className="text-zinc-500 mb-1">Role</dt>
                <dd className="text-zinc-100 capitalize">{user?.role}</dd>
              </div>
              <div>
                <dt className="text-zinc-500 mb-1">Premium</dt>
                <dd className={user?.is_premium ? 'text-emerald-400' : 'text-zinc-400'}>
                  {user?.is_premium ? 'Yes' : 'No'}
                </dd>
              </div>
            </dl>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">Bio</label>
            <textarea
              value={bioInput}
              onChange={e => setBioInput(e.target.value)}
              rows={3}
              className="w-full px-3 py-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-red-500 resize-none"
              placeholder="Tell us about yourself..."
            />
            <button
              onClick={() => updateMutation.mutate({ bio: bioInput })}
              disabled={updateMutation.isPending}
              className="mt-2 btn-primary text-sm"
            >
              Save Bio
            </button>
          </div>
        </div>
      )}

      {activeTab === 'favorites' && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="font-semibold mb-4">Your Favorites</h3>
          {favorites && Array.isArray(favorites) && favorites.length > 0 ? (
            <div className="space-y-2">
              {favorites.map((fav: { id: number; item_type: string; item_id: number; item_name: string }) => (
                <div key={fav.id} className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
                  <div>
                    <span className="text-sm text-zinc-100">{fav.item_name}</span>
                    <span className="ml-2 text-xs text-zinc-500 capitalize">{fav.item_type}</span>
                  </div>
                  <button
                    onClick={async () => {
                      await favoritesApi.remove(fav.item_type, fav.item_id)
                      queryClient.invalidateQueries({ queryKey: ['favorites'] })
                      toast.success('Removed from favorites')
                    }}
                    className="text-xs text-zinc-500 hover:text-red-400 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-zinc-500 text-sm">No favorites yet. Add teams and channels to your favorites.</p>
          )}
        </div>
      )}
    </div>
  )
}
