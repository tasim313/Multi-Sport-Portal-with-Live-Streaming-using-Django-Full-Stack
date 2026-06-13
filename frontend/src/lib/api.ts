import axios from 'axios'
import type {
  Match, Article, IPTVChannel, Team, League, Sport, LeagueTable,
  PaginatedResponse, SearchResults, AuthTokens, User, LiveCommentary,
  ScoreEvent, EPGProgram
} from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// JWT token injection
api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-refresh token on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const refresh = localStorage.getItem('refresh_token')
        if (!refresh) throw new Error('No refresh token')
        const { data } = await axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh })
        localStorage.setItem('access_token', data.access)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }
    return Promise.reject(error)
  }
)

// ─── Match APIs ───────────────────────────────────────────────────────────────
export const matchApi = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Match>>('/matches/', { params }).then(r => r.data),

  get: (id: number) =>
    api.get<Match>(`/matches/${id}/`).then(r => r.data),

  live: () =>
    api.get<Match[]>('/live-matches/').then(r => r.data),

  upcoming: () =>
    api.get<Match[]>('/upcoming-matches/').then(r => r.data),

  streams: (id: number) =>
    api.get(`/matches/${id}/streams/`).then(r => r.data),

  events: (id: number) =>
    api.get<ScoreEvent[]>(`/matches/${id}/events/`).then(r => r.data),

  commentary: (id: number, limit = 20) =>
    api.get<LiveCommentary[]>(`/matches/${id}/commentary/`, { params: { limit } }).then(r => r.data),

  summary: (id: number) =>
    api.get<{ summary: string }>(`/matches/${id}/summary/`).then(r => r.data),
}

// ─── IPTV APIs ────────────────────────────────────────────────────────────────
export const iptvApi = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<IPTVChannel>>('/iptv/channels/', { params }).then(r => r.data),

  get: (slug: string) =>
    api.get<IPTVChannel>(`/iptv/channels/${slug}/`).then(r => r.data),

  epg: (slug: string) =>
    api.get<EPGProgram[]>(`/iptv/channels/${slug}/epg/`).then(r => r.data),

  categories: async () => {
    const data = await api.get<PaginatedResponse<IPTVChannel>>('/iptv/channels/', {
      params: { page_size: 1 }
    }).then(r => r.data)
    return ['Sports', 'News', 'Entertainment', 'Movies', 'Kids', 'Music', 'International']
  },
}

// ─── Article APIs ─────────────────────────────────────────────────────────────
export const articleApi = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Article>>('/articles/', { params }).then(r => r.data),

  get: (slug: string) =>
    api.get<Article>(`/articles/${slug}/`).then(r => r.data),
}

// ─── Sports / Leagues / Teams ─────────────────────────────────────────────────
export const sportsApi = {
  sports: () =>
    api.get<PaginatedResponse<Sport>>('/sports/').then(r => r.data.results),

  leagues: (sport?: string) =>
    api.get<PaginatedResponse<League>>('/leagues/', { params: sport ? { sport } : {} }).then(r => r.data.results),

  teams: (league?: string) =>
    api.get<PaginatedResponse<Team>>('/teams/', { params: league ? { league } : {} }).then(r => r.data.results),

  standings: (leagueId: number, season?: string) =>
    api.get<PaginatedResponse<LeagueTable>>('/standings/', {
      params: { league: leagueId, ...(season ? { season } : {}) }
    }).then(r => r.data.results),
}

// ─── Auth APIs ────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    api.post<AuthTokens>('/auth/token/', { username, password }).then(r => r.data),

  register: (username: string, email: string, password: string) =>
    api.post('/auth/register/', { username, email, password }).then(r => r.data),

  profile: () =>
    api.get<User>('/auth/profile/').then(r => r.data),

  updateProfile: (data: Partial<User>) =>
    api.patch('/auth/profile/', data).then(r => r.data),

  refreshToken: (refresh: string) =>
    api.post<{ access: string }>('/auth/token/refresh/', { refresh }).then(r => r.data),
}

// ─── Favorites APIs ───────────────────────────────────────────────────────────
export const favoritesApi = {
  list: () =>
    api.get('/favorites/').then(r => r.data),

  add: (item_type: string, item_id: number, item_name?: string) =>
    api.post('/favorites/add/', { item_type, item_id, item_name }).then(r => r.data),

  remove: (item_type: string, item_id: number) =>
    api.delete(`/favorites/${item_type}/${item_id}/`).then(r => r.data),
}

// ─── Search ───────────────────────────────────────────────────────────────────
export const searchApi = {
  search: (q: string) =>
    api.get<SearchResults>('/search/', { params: { q } }).then(r => r.data),
}

// ─── Ads ──────────────────────────────────────────────────────────────────────
export const adsApi = {
  get: (slot: string, device = 'all') =>
    api.get('/ads/', { params: { slot, device } }).then(r => r.data),
}
