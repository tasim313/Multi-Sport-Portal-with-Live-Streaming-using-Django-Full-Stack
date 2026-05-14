export interface Sport {
  id: number
  name: string
  slug: string
  icon: string
  is_active: boolean
}

export interface League {
  id: number
  name: string
  slug: string
  season: string
  country: string
  logo: string
  sport: Sport
}

export interface Team {
  id: number
  name: string
  short_name: string
  slug: string
  logo: string
  colors: Record<string, string>
  country: string
  league: League
}

export interface StreamSource {
  id: number
  provider: string
  url: string
  embed_html: string
  is_iframe: boolean
  requires_auth: boolean
  priority: number
  is_active: boolean
}

export interface Match {
  id: number
  home_team: Team
  away_team: Team
  league: League
  venue: number | null
  start_time: string
  end_time: string | null
  status: 'scheduled' | 'live' | 'finished' | 'postponed' | 'cancelled'
  score_summary: {
    home?: number
    away?: number
    details?: Record<string, unknown>
  }
  metadata: Record<string, unknown>
  stream_sources: StreamSource[]
}

export interface ScoreEvent {
  id: number
  timestamp: string
  period: string
  minute: number | null
  event_type: string
  payload: Record<string, unknown>
  player_name: string
  team_side: 'home' | 'away' | ''
}

export interface LiveCommentary {
  id: number
  minute: number | null
  period: string
  rewritten_text: string
  is_key_event: boolean
  language: string
  source: string
  created_at: string
}

export interface Article {
  id: number
  title: string
  slug: string
  body: string
  excerpt: string
  author: string
  sport: Sport | null
  tags: string[]
  hero_image: string
  category: string
  published_at: string
  meta_description: string
  views_count: number
}

export interface IPTVChannel {
  id: number
  name: string
  slug: string
  stream_url: string
  logo: string
  category: string
  country: string
  country_code: string
  language: string
  is_featured: boolean
  is_working: boolean
  source_name: string
  source_url: string
  attribution: string
  current_program: {
    title: string
    description: string
    end_time: string
  } | null
}

export interface EPGProgram {
  id: number
  title: string
  description: string
  start_time: string
  end_time: string
  category: string
  language: string
  icon: string
  is_live: boolean
}

export interface LeagueTable {
  id: number
  team: Team
  season: string
  position: number
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  form: string
}

export interface UserFavorite {
  id: number
  item_type: 'team' | 'channel' | 'league' | 'player'
  item_id: number
  item_name: string
  created_at: string
}

export interface User {
  id: number
  username: string
  email: string
  role: string
  is_premium: boolean
  avatar: string
  bio: string
  favorite_teams: number[]
  notification_prefs: Record<string, boolean>
  watch_history: Array<{ match_id: number; watched_at: string }>
  date_joined: string
}

export interface AuthTokens {
  access: string
  refresh: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface SearchResults {
  matches: Match[]
  articles: Article[]
  teams: Team[]
  channels: IPTVChannel[]
}

// WebSocket message types
export interface WSMessage {
  type: 'match_data' | 'score_update' | 'status_update' | 'commentary_update' | 'commentary_history' | 'ticker_data' | 'ticker_update' | 'pong'
  data: unknown
}

export interface TickerMatch {
  id: number
  home: string
  away: string
  score: { home?: number; away?: number }
  league: string
  sport: string
  status: string
}
