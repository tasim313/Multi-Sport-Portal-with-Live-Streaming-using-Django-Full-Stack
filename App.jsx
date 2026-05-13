import React, { useState, useEffect, useContext, createContext, useCallback, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams, useNavigate, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import Hls from 'hls.js';
import { format, formatDistanceToNow } from 'date-fns';
import {
  Menu, X, Play, Calendar, Trophy,
  Bell, Search, User, Moon, Sun,
  ChevronRight, Clock, Tv, LogOut,
  AlertCircle, ArrowLeft, Filter
} from 'lucide-react';

// ─── API Setup ───────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:8000/api';

const api = axios.create({ baseURL: API_BASE, timeout: 10000 });

// Inject JWT token on every request
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// Auto-refresh token on 401
api.interceptors.response.use(
  r => r,
  async err => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      }
    }
    return Promise.reject(err);
  }
);

// ─── Auth Context ─────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      api.get('/auth/profile/')
        .then(r => setUser(r.data))
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username, password) => {
    const { data } = await api.post('/auth/token/', { username, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    const profile = await api.get('/auth/profile/');
    setUser(profile.data);
    return profile.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const register = async (username, email, password) => {
    await api.post('/auth/register/', { username, email, password });
    return login(username, password);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// ─── API Hooks ────────────────────────────────────────────────────────────────

const useWebSocket = (matchId) => {
  const [lastEvent, setLastEvent] = useState(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!matchId) return;
    const wsBase = import.meta.env.PROD ? `wss://${window.location.host}` : 'ws://localhost:8000';
    const ws = new WebSocket(`${wsBase}/ws/matches/${matchId}/`);
    ws.onmessage = e => {
      const data = JSON.parse(e.data);
      if (data.type === 'score_update') {
        setLastEvent(data.data);
        queryClient.invalidateQueries(['match', matchId]);
        queryClient.invalidateQueries(['matches']);
      }
    };
    return () => ws.close();
  }, [matchId, queryClient]);

  return { lastEvent };
};

const useMatches = (filters = {}) =>
  useQuery(['matches', filters], async () => {
    const { data } = await api.get('/matches/', { params: filters });
    return data;
  }, { refetchInterval: 30000 });

const useMatch = id =>
  useQuery(['match', id], async () => {
    const { data } = await api.get(`/matches/${id}/`);
    return data;
  }, { enabled: !!id });

const useSports = () =>
  useQuery('sports', async () => {
    const { data } = await api.get('/sports/');
    return data;
  });

const useArticles = (params = {}) =>
  useQuery(['articles', params], async () => {
    const { data } = await api.get('/articles/', { params });
    return data;
  });

const useArticle = slug =>
  useQuery(['article', slug], async () => {
    const { data } = await api.get(`/articles/${slug}/`);
    return data;
  }, { enabled: !!slug });

const useSearch = q =>
  useQuery(['search', q], async () => {
    const { data } = await api.get('/search/', { params: { q } });
    return data;
  }, { enabled: q?.length >= 2 });

const useIPTVChannels = (filters = {}) =>
  useQuery(['iptv-channels', filters], async () => {
    const { data } = await api.get('/iptv/channels/', { params: filters });
    return data;
  }, { keepPreviousData: true, staleTime: 60000 });

// ─── Shared Components ────────────────────────────────────────────────────────

const LiveBadge = () => (
  <span className="inline-flex items-center bg-red-500 text-white px-2 py-0.5 rounded-full text-xs font-semibold">
    <span className="w-1.5 h-1.5 bg-white rounded-full mr-1 animate-pulse" />
    LIVE
  </span>
);

const StatusBadge = ({ status, startTime }) => {
  if (status === 'live') return <LiveBadge />;
  if (status === 'scheduled') return (
    <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-0.5 rounded-full text-xs font-medium">
      {format(new Date(startTime), 'HH:mm')}
    </span>
  );
  if (status === 'finished') return (
    <span className="bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded-full text-xs font-medium">FT</span>
  );
  return <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full text-xs font-medium capitalize">{status}</span>;
};

const MatchCard = ({ match, compact = false }) => {
  const isLive = match.status === 'live';
  return (
    <div className={`bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 hover:shadow-lg transition-all ${compact ? 'p-3' : 'p-5'}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-500 dark:text-gray-400 truncate mr-2">{match.league?.name}</span>
        <StatusBadge status={match.status} startTime={match.start_time} />
      </div>

      <div className="flex items-center justify-between gap-2">
        <div className="flex-1 text-center">
          <div
            className="w-10 h-10 rounded-full mx-auto mb-1.5 flex items-center justify-center text-white text-sm font-bold"
            style={{ backgroundColor: match.home_team?.colors?.primary || '#6B7280' }}
          >
            {match.home_team?.short_name?.charAt(0)}
          </div>
          <p className="text-xs font-semibold truncate">{match.home_team?.short_name}</p>
        </div>

        <div className="text-center px-2 min-w-[60px]">
          {isLive || match.status === 'finished' ? (
            <div className="text-xl font-bold text-gray-900 dark:text-white">
              {match.score_summary?.home ?? 0}
              <span className="text-gray-400 mx-1">-</span>
              {match.score_summary?.away ?? 0}
            </div>
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {format(new Date(match.start_time), 'MMM d')}
            </div>
          )}
          {match.stream_sources?.length > 0 && (
            <div className="flex items-center justify-center text-green-600 mt-1 text-xs">
              <Tv className="w-3 h-3 mr-0.5" /> Watch
            </div>
          )}
        </div>

        <div className="flex-1 text-center">
          <div
            className="w-10 h-10 rounded-full mx-auto mb-1.5 flex items-center justify-center text-white text-sm font-bold"
            style={{ backgroundColor: match.away_team?.colors?.primary || '#6B7280' }}
          >
            {match.away_team?.short_name?.charAt(0)}
          </div>
          <p className="text-xs font-semibold truncate">{match.away_team?.short_name}</p>
        </div>
      </div>
    </div>
  );
};

const ArticleCard = ({ article, featured = false }) => (
  <Link to={`/news/${article.slug}`} className="group block">
    <div className={`bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden hover:shadow-lg transition-all ${featured ? 'md:flex' : ''}`}>
      {article.hero_image && (
        <div className={`bg-gray-200 dark:bg-slate-700 ${featured ? 'md:w-2/5 h-48 md:h-auto' : 'h-44'}`}>
          <img src={article.hero_image} alt={article.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
        </div>
      )}
      <div className="p-4 flex-1">
        <div className="flex flex-wrap gap-1 mb-2">
          {article.tags?.slice(0, 2).map(t => (
            <span key={t} className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs px-2 py-0.5 rounded-full">{t}</span>
          ))}
        </div>
        <h3 className={`font-bold text-gray-900 dark:text-white group-hover:text-green-600 transition-colors ${featured ? 'text-xl' : 'text-base'} mb-2 line-clamp-2`}>
          {article.title}
        </h3>
        {article.excerpt && (
          <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">{article.excerpt}</p>
        )}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>By {article.author}</span>
          {article.published_at && <span>{formatDistanceToNow(new Date(article.published_at))} ago</span>}
        </div>
      </div>
    </div>
  </Link>
);

const LoadingGrid = ({ count = 3 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="animate-pulse bg-white dark:bg-slate-800 rounded-xl p-5 border border-gray-200 dark:border-slate-700">
        <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2 mb-4" />
        <div className="flex justify-between items-center">
          <div className="w-10 h-10 bg-gray-200 dark:bg-slate-700 rounded-full" />
          <div className="h-6 bg-gray-200 dark:bg-slate-700 rounded w-16" />
          <div className="w-10 h-10 bg-gray-200 dark:bg-slate-700 rounded-full" />
        </div>
      </div>
    ))}
  </div>
);

// ─── Header ───────────────────────────────────────────────────────────────────

const Header = ({ darkMode, toggleDarkMode }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQ, setSearchQ] = useState('');
  const { data: sports } = useSports();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleSearch = e => {
    e.preventDefault();
    if (searchQ.trim().length >= 2) {
      navigate(`/search?q=${encodeURIComponent(searchQ.trim())}`);
      setSearchOpen(false);
      setSearchQ('');
    }
  };

  return (
    <header className="bg-white dark:bg-slate-800 shadow-sm sticky top-0 z-50 border-b border-gray-200 dark:border-slate-700">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 bg-gradient-to-br from-green-600 to-amber-500 rounded-lg flex items-center justify-center">
              <Trophy className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-green-600">Sports Portal</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
            <Link to="/live" className="flex items-center gap-1 text-gray-700 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400 transition-colors">
              <Play className="w-3.5 h-3.5 text-red-500" /> Live
            </Link>
            <Link to="/tv" className="flex items-center gap-1 text-gray-700 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400 transition-colors">
              <Tv className="w-3.5 h-3.5 text-green-600" /> TV Channels
            </Link>
            {sports?.results?.map(s => (
              <Link key={s.slug} to={`/sport/${s.slug}`} className="text-gray-700 dark:text-gray-300 hover:text-green-600 dark:hover:text-green-400 transition-colors">
                {s.icon} {s.name}
              </Link>
            ))}
            {!sports?.results && (
              <>
                <Link to="/sport/cricket" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">🏏 Cricket</Link>
                <Link to="/sport/football" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">⚽ Football</Link>
                <Link to="/sport/tennis" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">🎾 Tennis</Link>
              </>
            )}
            <Link to="/news" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">News</Link>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {searchOpen ? (
              <form onSubmit={handleSearch} className="flex items-center">
                <input
                  autoFocus
                  value={searchQ}
                  onChange={e => setSearchQ(e.target.value)}
                  placeholder="Search matches, news..."
                  className="border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-lg px-3 py-1.5 text-sm w-48 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button type="button" onClick={() => setSearchOpen(false)} className="ml-1 p-1 text-gray-500">
                  <X className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <button onClick={() => setSearchOpen(true)} className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 transition-colors">
                <Search className="w-5 h-5" />
              </button>
            )}

            <button onClick={toggleDarkMode} className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 transition-colors">
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {user ? (
              <div className="relative group">
                <button className="flex items-center gap-1 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-green-600">
                  <User className="w-5 h-5" />
                  <span className="hidden md:block">{user.username}</span>
                </button>
                <div className="absolute right-0 top-8 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl shadow-lg w-44 py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                  <Link to="/profile" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700">Profile</Link>
                  <button onClick={logout} className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50 dark:hover:bg-slate-700 flex items-center gap-2">
                    <LogOut className="w-3.5 h-3.5" /> Sign Out
                  </button>
                </div>
              </div>
            ) : (
              <Link to="/login" className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors">
                Sign In
              </Link>
            )}

            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-2 text-gray-600 dark:text-gray-400">
              {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-gray-200 dark:border-slate-700 py-3 space-y-1">
            {[
              { to: '/live', label: '🔴 Live' },
              { to: '/tv', label: '📺 TV Channels' },
              { to: '/sport/cricket', label: '🏏 Cricket' },
              { to: '/sport/football', label: '⚽ Football' },
              { to: '/sport/tennis', label: '🎾 Tennis' },
              { to: '/news', label: '📰 News' },
            ].map(({ to, label }) => (
              <Link key={to} to={to} onClick={() => setMenuOpen(false)}
                className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700 rounded-lg">
                {label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </header>
  );
};

// ─── Pages ────────────────────────────────────────────────────────────────────

const HomePage = () => {
  const { data: liveData, isLoading: loadingLive } = useMatches({ status: 'live' });
  const { data: upcomingData, isLoading: loadingUpcoming } = useMatches({ status: 'upcoming' });
  const liveMatches = liveData?.results || liveData || [];
  const upcomingMatches = upcomingData?.results || upcomingData || [];
  const { data: articles } = useArticles({ page_size: 4 });
  const articleList = articles?.results || articles || [];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Hero */}
      <div className="relative bg-gradient-to-r from-green-700 via-green-600 to-amber-500 rounded-2xl p-8 mb-10 text-white overflow-hidden">
        <div className="relative z-10">
          <h1 className="text-3xl md:text-4xl font-bold mb-3">Live Sports, Right Now</h1>
          <p className="text-lg opacity-90 mb-6">Watch cricket, football & tennis with real-time scores</p>
          <div className="flex gap-3 flex-wrap">
            <Link to="/live" className="bg-white text-green-700 font-semibold px-5 py-2 rounded-full hover:bg-green-50 transition-colors flex items-center gap-2">
              <Play className="w-4 h-4" /> Watch Live
            </Link>
            <Link to="/news" className="border border-white text-white font-semibold px-5 py-2 rounded-full hover:bg-white/10 transition-colors">
              Latest News
            </Link>
          </div>
        </div>
        <div className="absolute right-0 top-0 w-64 h-full opacity-10 flex items-center justify-center text-9xl">🏆</div>
      </div>

      {/* Live Matches */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Play className="w-5 h-5 text-red-500" /> Live Now
          </h2>
          <Link to="/live" className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1">
            View all <ChevronRight className="w-4 h-4" />
          </Link>
        </div>
        {loadingLive ? <LoadingGrid /> : liveMatches.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {liveMatches.slice(0, 6).map(m => (
              <Link key={m.id} to={`/match/${m.id}`}><MatchCard match={m} /></Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800 rounded-xl">
            No live matches right now. Check the schedule below.
          </div>
        )}
      </section>

      {/* Upcoming */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-500" /> Upcoming
          </h2>
        </div>
        {loadingUpcoming ? <LoadingGrid /> : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {upcomingMatches.slice(0, 6).map(m => (
              <Link key={m.id} to={`/match/${m.id}`}><MatchCard match={m} /></Link>
            ))}
          </div>
        )}
      </section>

      {/* Latest News */}
      {articleList.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Latest News</h2>
            <Link to="/news" className="text-sm text-green-600 hover:text-green-700 flex items-center gap-1">
              All news <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {articleList.slice(0, 4).map((a, i) => (
              <ArticleCard key={a.id} article={a} featured={i === 0} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

const SportPage = () => {
  const { sport } = useParams();
  const [statusFilter, setStatusFilter] = useState('');
  const { data: liveData } = useMatches({ status: 'live', sport });
  const { data: upcomingData } = useMatches({ status: 'upcoming', sport });
  const { data: finishedData } = useMatches({ status: 'finished', sport });

  const sportLabels = { cricket: '🏏 Cricket', football: '⚽ Football', tennis: '🎾 Tennis' };
  const label = sportLabels[sport] || sport;

  const filteredData = statusFilter === 'live' ? liveData
    : statusFilter === 'upcoming' ? upcomingData
    : statusFilter === 'finished' ? finishedData
    : null;

  const allMatches = [
    ...(liveData?.results || liveData || []),
    ...(upcomingData?.results || upcomingData || []),
  ];
  const displayMatches = filteredData
    ? (filteredData?.results || filteredData || [])
    : allMatches;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">{label}</h1>
        <p className="text-gray-600 dark:text-gray-400">Live scores, upcoming matches and results</p>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {[
          { value: '', label: 'All' },
          { value: 'live', label: '🔴 Live' },
          { value: 'upcoming', label: 'Upcoming' },
          { value: 'finished', label: 'Finished' },
        ].map(({ value, label: l }) => (
          <button
            key={value}
            onClick={() => setStatusFilter(value)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              statusFilter === value
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600'
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {displayMatches.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {displayMatches.map(m => (
            <Link key={m.id} to={`/match/${m.id}`}><MatchCard match={m} /></Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800 rounded-xl">
          No {statusFilter || ''} matches found for {label}
        </div>
      )}
    </div>
  );
};

const LivePage = () => {
  const { data, isLoading } = useMatches({ status: 'live' });
  const matches = data?.results || data || [];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
        <Play className="w-7 h-7 text-red-500" /> Live Matches
      </h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">Matches happening right now</p>
      {isLoading ? <LoadingGrid /> : matches.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {matches.map(m => (
            <Link key={m.id} to={`/match/${m.id}`}><MatchCard match={m} /></Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800 rounded-xl">
          <Play className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-lg font-medium">No live matches right now</p>
          <p className="text-sm mt-1">Check back soon or browse upcoming matches</p>
          <Link to="/" className="mt-4 inline-block text-green-600 hover:underline text-sm">View schedule →</Link>
        </div>
      )}
    </div>
  );
};

const IPTVPlayer = ({ channel }) => {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !channel?.stream_url) return undefined;

    let hls;
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = channel.stream_url;
    } else if (Hls.isSupported()) {
      hls = new Hls({ enableWorker: true });
      hls.loadSource(channel.stream_url);
      hls.attachMedia(video);
    }

    return () => {
      if (hls) hls.destroy();
      if (video) video.removeAttribute('src');
    };
  }, [channel]);

  return (
    <div className="bg-black aspect-video rounded-xl overflow-hidden border border-gray-200 dark:border-slate-700">
      {channel ? (
        <video
          ref={videoRef}
          className="w-full h-full"
          controls
          playsInline
          poster={channel.logo || undefined}
        />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center text-white">
          <Tv className="w-12 h-12 opacity-40 mb-3" />
          <p className="text-sm opacity-70">Select a channel to start watching</p>
        </div>
      )}
    </div>
  );
};

const TVChannelsPage = () => {
  const [filters, setFilters] = useState({ category: 'Sports' });
  const [selected, setSelected] = useState(null);
  const { data, isLoading, isError } = useIPTVChannels(filters);
  const channels = data?.results || data || [];

  useEffect(() => {
    if (!selected && channels.length > 0) setSelected(channels[0]);
  }, [channels, selected]);

  const updateFilter = (key, value) => {
    setSelected(null);
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Tv className="w-7 h-7 text-green-600" /> TV Channels
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Public IPTV channels from iptv-org. Streams play from their original public URLs.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <IPTVPlayer channel={selected} />
          {selected && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-4">
              <div className="flex items-start gap-3">
                {selected.logo ? (
                  <img src={selected.logo} alt="" className="w-12 h-12 object-contain bg-gray-50 dark:bg-slate-700 rounded-lg p-1" />
                ) : (
                  <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900 flex items-center justify-center">
                    <Tv className="w-6 h-6 text-green-700 dark:text-green-300" />
                  </div>
                )}
                <div className="min-w-0">
                  <h2 className="font-bold text-lg text-gray-900 dark:text-white">{selected.name}</h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {[selected.category, selected.country_code || selected.country, selected.language].filter(Boolean).join(' · ') || 'Public channel'}
                  </p>
                  <p className="text-xs text-gray-400 mt-2">{selected.attribution}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-4">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Search</label>
                <input
                  value={filters.q || ''}
                  onChange={e => updateFilter('q', e.target.value)}
                  placeholder="Channel name"
                  className="w-full border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => updateFilter('category', 'Sports')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium ${filters.category === 'Sports' ? 'bg-green-600 text-white' : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300'}`}
                >
                  Sports
                </button>
                <button
                  type="button"
                  onClick={() => updateFilter('category', '')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium ${!filters.category ? 'bg-green-600 text-white' : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300'}`}
                >
                  All
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input
                  value={filters.country || ''}
                  onChange={e => updateFilter('country', e.target.value)}
                  placeholder="Country"
                  className="border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <input
                  value={filters.language || ''}
                  onChange={e => updateFilter('language', e.target.value)}
                  placeholder="Language"
                  className="border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 dark:border-slate-700">
              <h3 className="font-semibold text-gray-900 dark:text-white">Channels</h3>
            </div>
            <div className="max-h-[560px] overflow-y-auto">
              {isLoading && <div className="p-4 text-sm text-gray-500">Loading channels...</div>}
              {isError && <div className="p-4 text-sm text-red-600">Could not load channels.</div>}
              {!isLoading && channels.length === 0 && (
                <div className="p-4 text-sm text-gray-500">No channels found. Import channels from the admin command first.</div>
              )}
              {channels.map(channel => (
                <button
                  type="button"
                  key={channel.id}
                  onClick={() => setSelected(channel)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-100 dark:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors ${selected?.id === channel.id ? 'bg-green-50 dark:bg-green-900/20' : ''}`}
                >
                  <div className="flex items-center gap-3">
                    {channel.logo ? (
                      <img src={channel.logo} alt="" className="w-9 h-9 object-contain bg-gray-50 dark:bg-slate-700 rounded p-1" />
                    ) : (
                      <div className="w-9 h-9 bg-gray-100 dark:bg-slate-700 rounded flex items-center justify-center">
                        <Tv className="w-4 h-4 text-gray-400" />
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="font-medium text-sm text-gray-900 dark:text-white truncate">{channel.name}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {[channel.category, channel.country_code || channel.country].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

const MatchDetail = () => {
  const { matchId } = useParams();
  const { data: match, isLoading } = useMatch(matchId);
  const { lastEvent } = useWebSocket(matchId);
  const [activeTab, setActiveTab] = useState('stream');

  if (isLoading) return (
    <div className="container mx-auto px-4 py-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-slate-700 rounded w-1/3" />
        <div className="h-64 bg-gray-200 dark:bg-slate-700 rounded-xl" />
      </div>
    </div>
  );

  if (!match) return (
    <div className="container mx-auto px-4 py-8 text-center">
      <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Match not found</h1>
      <Link to="/" className="mt-4 inline-flex items-center gap-1 text-green-600 hover:underline">
        <ArrowLeft className="w-4 h-4" /> Back to Home
      </Link>
    </div>
  );

  const activeStream = match.stream_sources?.find(s => s.is_active);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Match header */}
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">{match.league?.name}</p>
            {match.venue && <p className="text-xs text-gray-400">{match.venue}</p>}
          </div>
          <StatusBadge status={match.status} startTime={match.start_time} />
        </div>

        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 text-center">
            <div
              className="w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl font-bold"
              style={{ backgroundColor: match.home_team?.colors?.primary || '#6B7280' }}
            >
              {match.home_team?.short_name?.charAt(0)}
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{match.home_team?.name}</h3>
          </div>

          <div className="text-center">
            <div className="text-4xl font-bold text-gray-900 dark:text-white mb-1">
              {match.score_summary?.home ?? 0}
              <span className="text-gray-400 mx-2">-</span>
              {match.score_summary?.away ?? 0}
            </div>
            <p className="text-xs text-gray-500">{format(new Date(match.start_time), 'MMM dd, yyyy · HH:mm')}</p>
          </div>

          <div className="flex-1 text-center">
            <div
              className="w-16 h-16 rounded-full mx-auto mb-2 flex items-center justify-center text-white text-xl font-bold"
              style={{ backgroundColor: match.away_team?.colors?.primary || '#6B7280' }}
            >
              {match.away_team?.short_name?.charAt(0)}
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{match.away_team?.name}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tabs */}
          {activeStream && (
            <div className="flex gap-1 bg-gray-100 dark:bg-slate-700 p-1 rounded-lg w-fit">
              {['stream', 'events'].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium capitalize transition-colors ${
                    activeTab === tab
                      ? 'bg-white dark:bg-slate-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}>
                  {tab === 'stream' ? '📺 Stream' : '📋 Events'}
                </button>
              ))}
            </div>
          )}

          {/* Stream */}
          {activeTab === 'stream' && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 overflow-hidden">
              {activeStream ? (
                <div className="aspect-video bg-black">
                  {activeStream.embed_html ? (
                    <div dangerouslySetInnerHTML={{ __html: activeStream.embed_html }} className="w-full h-full" />
                  ) : (
                    <iframe
                      src={activeStream.url}
                      className="w-full h-full"
                      frameBorder="0"
                      allowFullScreen
                      sandbox="allow-scripts allow-same-origin allow-presentation"
                      title="Live Stream"
                    />
                  )}
                </div>
              ) : (
                <div className="aspect-video flex flex-col items-center justify-center bg-gray-900 text-white">
                  <Tv className="w-12 h-12 opacity-30 mb-3" />
                  <p className="font-medium opacity-60">No stream available</p>
                  <p className="text-xs opacity-40 mt-1">
                    {match.status === 'scheduled' ? `Stream starts at ${format(new Date(match.start_time), 'HH:mm')}` : 'Stream has ended'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Events timeline */}
          {activeTab === 'events' && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-4">
              <h3 className="font-semibold mb-3">Match Events</h3>
              {lastEvent ? (
                <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <span className="text-xl">{lastEvent.event_type === 'goal' ? '⚽' : lastEvent.event_type === 'wicket' ? '🏏' : '📝'}</span>
                  <div>
                    <p className="font-medium capitalize">{lastEvent.event_type?.replace('_', ' ')}</p>
                    <p className="text-xs text-gray-500">{formatDistanceToNow(new Date(lastEvent.timestamp))} ago</p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-sm text-center py-6">No events yet</p>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {lastEvent && (
            <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-4">
              <h3 className="font-semibold mb-3 text-sm">Latest Event</h3>
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3">
                <p className="font-medium capitalize text-sm">{lastEvent.event_type?.replace('_', ' ')}</p>
                <p className="text-xs text-gray-500 mt-1">{formatDistanceToNow(new Date(lastEvent.timestamp))} ago</p>
              </div>
            </div>
          )}

          {/* Match info */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 p-4">
            <h3 className="font-semibold mb-3 text-sm">Match Info</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Sport</dt>
                <dd className="font-medium">{match.league?.sport?.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">League</dt>
                <dd className="font-medium text-right">{match.league?.name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Date</dt>
                <dd className="font-medium">{format(new Date(match.start_time), 'MMM dd, yyyy')}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Time</dt>
                <dd className="font-medium">{format(new Date(match.start_time), 'HH:mm')}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Streams</dt>
                <dd className="font-medium text-green-600">{match.stream_sources?.filter(s => s.is_active).length || 0} active</dd>
              </div>
            </dl>
          </div>

          {/* Ad slot */}
          <div className="bg-gray-100 dark:bg-slate-700 rounded-xl p-4 text-center">
            <p className="text-xs text-gray-500 mb-2">Advertisement</p>
            <div className="h-32 bg-gray-200 dark:bg-slate-600 rounded-lg flex items-center justify-center text-gray-400 text-xs">Ad Space</div>
          </div>
        </div>
      </div>
    </div>
  );
};

const NewsPage = () => {
  const { data, isLoading } = useArticles();
  const articles = data?.results || data || [];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Sports News</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-8">Latest articles, previews and analysis</p>
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse h-40 bg-gray-200 dark:bg-slate-700 rounded-xl" />
          ))}
        </div>
      ) : articles.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map((a, i) => <ArticleCard key={a.id} article={a} featured={i === 0 && articles.length > 2} />)}
        </div>
      ) : (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800 rounded-xl">
          No articles published yet.
        </div>
      )}
    </div>
  );
};

const ArticleDetail = () => {
  const { slug } = useParams();
  const { data: article, isLoading, isError } = useArticle(slug);

  if (isLoading) return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 dark:bg-slate-700 rounded w-3/4" />
        <div className="h-64 bg-gray-200 dark:bg-slate-700 rounded-xl" />
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-4 bg-gray-200 dark:bg-slate-700 rounded" />)}
        </div>
      </div>
    </div>
  );

  if (isError || !article) return (
    <div className="container mx-auto px-4 py-8 text-center">
      <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
      <h1 className="text-2xl font-bold">Article not found</h1>
      <Link to="/news" className="mt-4 inline-flex items-center gap-1 text-green-600 hover:underline">
        <ArrowLeft className="w-4 h-4" /> Back to News
      </Link>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-3xl mx-auto">
        <Link to="/news" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-green-600 mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to News
        </Link>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          {article.tags?.map(t => (
            <span key={t} className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs px-2.5 py-1 rounded-full">{t}</span>
          ))}
        </div>

        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">{article.title}</h1>

        <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mb-6 pb-6 border-b border-gray-200 dark:border-slate-700">
          <span>By <strong className="text-gray-700 dark:text-gray-300">{article.author}</strong></span>
          {article.published_at && (
            <>
              <span>·</span>
              <span>{format(new Date(article.published_at), 'MMMM dd, yyyy')}</span>
            </>
          )}
        </div>

        {article.hero_image && (
          <img src={article.hero_image} alt={article.title} className="w-full h-72 md:h-96 object-cover rounded-xl mb-8" />
        )}

        {article.excerpt && (
          <p className="text-lg text-gray-600 dark:text-gray-400 italic mb-6 border-l-4 border-green-500 pl-4">{article.excerpt}</p>
        )}

        <div className="prose dark:prose-invert max-w-none text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
          {article.body}
        </div>
      </div>
    </div>
  );
};

const SearchPage = () => {
  const navigate = useNavigate();
  const params = new URLSearchParams(window.location.search);
  const initialQ = params.get('q') || '';
  const [q, setQ] = useState(initialQ);
  const [submitted, setSubmitted] = useState(initialQ);
  const { data, isLoading } = useSearch(submitted);

  const handleSubmit = e => {
    e.preventDefault();
    setSubmitted(q);
    navigate(`/search?q=${encodeURIComponent(q)}`, { replace: true });
  };

  const hasResults = data && (data.matches?.length || data.articles?.length || data.teams?.length);

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Search</h1>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-8">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          placeholder="Search matches, teams, articles..."
          className="flex-1 border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button type="submit" className="bg-green-600 hover:bg-green-700 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors flex items-center gap-2">
          <Search className="w-4 h-4" /> Search
        </button>
      </form>

      {isLoading && <div className="text-center py-10 text-gray-500">Searching...</div>}

      {!isLoading && submitted.length >= 2 && !hasResults && (
        <div className="text-center py-16 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-slate-800 rounded-xl">
          No results found for "<strong>{submitted}</strong>"
        </div>
      )}

      {data?.matches?.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Matches</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {data.matches.map(m => (
              <Link key={m.id} to={`/match/${m.id}`}><MatchCard match={m} /></Link>
            ))}
          </div>
        </section>
      )}

      {data?.teams?.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Teams</h2>
          <div className="flex flex-wrap gap-3">
            {data.teams.map(t => (
              <Link key={t.id} to={`/sport/${t.league?.sport?.slug}`}
                className="flex items-center gap-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl px-4 py-2 hover:shadow-md transition-all">
                <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                  style={{ backgroundColor: t.colors?.primary || '#6B7280' }}>
                  {t.short_name?.charAt(0)}
                </div>
                <div>
                  <p className="font-medium text-sm">{t.name}</p>
                  <p className="text-xs text-gray-500">{t.league?.name}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {data?.articles?.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Articles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {data.articles.map(a => <ArticleCard key={a.id} article={a} />)}
          </div>
        </section>
      )}
    </div>
  );
};

const LoginPage = () => {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(form.username, form.password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-gradient-to-br from-green-600 to-amber-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Sign In</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Welcome back to Sports Portal</p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 p-8 shadow-sm">
          {error && (
            <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm p-3 rounded-lg mb-4">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
              <input
                type="text"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
                className="w-full border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
              <input
                type="password"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                required
                className="w-full border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-xl transition-colors"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
            Don't have an account?{' '}
            <Link to="/register" className="text-green-600 hover:underline font-medium">Sign Up</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

const RegisterPage = () => {
  const { register, user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    if (form.password !== form.confirm) { setError('Passwords do not match'); return; }
    if (form.password.length < 8) { setError('Password must be at least 8 characters'); return; }
    setLoading(true);
    try {
      await register(form.username, form.email, form.password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-gradient-to-br from-green-600 to-amber-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Trophy className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Create Account</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Join Sports Portal for free</p>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 p-8 shadow-sm">
          {error && (
            <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm p-3 rounded-lg mb-4">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {[
              { key: 'username', label: 'Username', type: 'text' },
              { key: 'email', label: 'Email', type: 'email' },
              { key: 'password', label: 'Password', type: 'password' },
              { key: 'confirm', label: 'Confirm Password', type: 'password' },
            ].map(({ key, label, type }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
                <input
                  type={type}
                  value={form[key]}
                  onChange={e => setForm({ ...form, [key]: e.target.value })}
                  required
                  className="w-full border border-gray-300 dark:border-slate-600 dark:bg-slate-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            ))}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold py-2.5 rounded-xl transition-colors"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-green-600 hover:underline font-medium">Sign In</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

const ProfilePage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return <Navigate to="/login" replace />;

  const roleColors = {
    sysadmin: 'bg-red-100 text-red-800',
    streamer_admin: 'bg-purple-100 text-purple-800',
    editor: 'bg-blue-100 text-blue-800',
    subscriber: 'bg-amber-100 text-amber-800',
    registered: 'bg-green-100 text-green-800',
    anonymous: 'bg-gray-100 text-gray-800',
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">My Profile</h1>

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 p-6 mb-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-green-600 to-amber-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            {user.username?.charAt(0).toUpperCase()}
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{user.username}</h2>
            <p className="text-gray-500 text-sm">{user.email}</p>
            <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium capitalize ${roleColors[user.role] || 'bg-gray-100 text-gray-800'}`}>
              {user.role?.replace('_', ' ')}
            </span>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-4 text-sm border-t border-gray-100 dark:border-slate-700 pt-4">
          <div>
            <dt className="text-gray-500">Member since</dt>
            <dd className="font-medium">{user.date_joined ? format(new Date(user.date_joined), 'MMMM yyyy') : 'N/A'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Account type</dt>
            <dd className="font-medium">{user.is_premium ? '⭐ Premium' : 'Free'}</dd>
          </div>
        </dl>
      </div>

      {/* Subscription CTA for free users */}
      {!user.is_premium && (
        <div className="bg-gradient-to-r from-green-600 to-amber-500 rounded-2xl p-6 text-white mb-6">
          <h3 className="text-lg font-bold mb-2">Upgrade to Premium</h3>
          <p className="text-sm opacity-90 mb-4">Get access to all live streams, no ads, and exclusive content.</p>
          <ul className="text-sm space-y-1 mb-4 opacity-90">
            {['All live streams unlocked', 'Ad-free experience', 'HD quality streams', 'Early access to news'].map(f => (
              <li key={f} className="flex items-center gap-2">✓ {f}</li>
            ))}
          </ul>
          <button className="bg-white text-green-700 font-semibold px-5 py-2 rounded-full hover:bg-green-50 transition-colors">
            Upgrade Now
          </button>
        </div>
      )}

      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 p-6">
        <h3 className="font-semibold mb-4">Account Actions</h3>
        <button
          onClick={() => { logout(); navigate('/'); }}
          className="flex items-center gap-2 text-red-600 hover:text-red-700 text-sm font-medium"
        >
          <LogOut className="w-4 h-4" /> Sign Out
        </button>
      </div>
    </div>
  );
};

const NotFoundPage = () => (
  <div className="container mx-auto px-4 py-20 text-center">
    <div className="text-8xl mb-4">🏟️</div>
    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Page Not Found</h1>
    <p className="text-gray-500 dark:text-gray-400 mb-6">This page doesn't exist or has been moved.</p>
    <Link to="/" className="bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors">
      Back to Home
    </Link>
  </div>
);

// ─── Main App ─────────────────────────────────────────────────────────────────

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1 },
  },
});

const AppInner = () => {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors">
      <Header darkMode={darkMode} toggleDarkMode={() => setDarkMode(d => !d)} />
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/live" element={<LivePage />} />
          <Route path="/tv" element={<TVChannelsPage />} />
          <Route path="/sport/:sport" element={<SportPage />} />
          <Route path="/match/:matchId" element={<MatchDetail />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/news/:slug" element={<ArticleDetail />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          {/* Legacy sport routes */}
          <Route path="/cricket" element={<Navigate to="/sport/cricket" replace />} />
          <Route path="/football" element={<Navigate to="/sport/football" replace />} />
          <Route path="/tennis" element={<Navigate to="/sport/tennis" replace />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <footer className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 py-8 mt-16">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500 dark:text-gray-400">
          <p className="mb-1">© 2025 Sports Portal. All rights reserved.</p>
          <p className="flex items-center justify-center gap-4">
            <Link to="/sport/cricket" className="hover:text-green-600">🏏 Cricket</Link>
            <Link to="/sport/football" className="hover:text-green-600">⚽ Football</Link>
            <Link to="/sport/tennis" className="hover:text-green-600">🎾 Tennis</Link>
            <Link to="/news" className="hover:text-green-600">News</Link>
          </p>
        </div>
      </footer>
    </div>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <Router>
        <AppInner />
      </Router>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
