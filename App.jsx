import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery, useQueryClient } from 'react-query';
import axios from 'axios';
import { format, formatDistanceToNow } from 'date-fns';
import { 
    Menu, X, Play, Users, Calendar, Trophy, 
    Bell, Search, User, Settings, Moon, Sun,
    ChevronRight, Clock, MapPin, Tv
} from 'lucide-react';
import './App.css';

// API Configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? '/api' 
    : 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
});

// WebSocket Hook
const useWebSocket = (matchId) => {
    const [socket, setSocket] = useState(null);
    const [lastEvent, setLastEvent] = useState(null);
    const queryClient = useQueryClient();
    
    useEffect(() => {
        if (!matchId) return;
        
        const wsUrl = `ws://localhost:8000/ws/matches/${matchId}/`;
        const ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
            console.log('WebSocket connected for match:', matchId);
            setSocket(ws);
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'score_update') {
                setLastEvent(data.data);
                queryClient.invalidateQueries(['match', matchId]);
                queryClient.invalidateQueries(['matches']);
            }
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setSocket(null);
        };
        
        return () => {
            ws.close();
        };
    }, [matchId, queryClient]);
    
    return { socket, lastEvent };
};

// API Hooks
const useMatches = (filters = {}) => {
    return useQuery(['matches', filters], async () => {
        const params = new URLSearchParams(filters);
        const response = await api.get(`/matches/?${params}`);
        return response.data;
    }, {
        refetchInterval: 30000,
    });
};

const useMatch = (matchId) => {
    return useQuery(['match', matchId], async () => {
        const response = await api.get(`/matches/${matchId}/`);
        return response.data;
    }, {
        enabled: !!matchId,
    });
};

const useSports = () => {
    return useQuery('sports', async () => {
        const response = await api.get('/sports/');
        return response.data;
    });
};

// Components
const Header = ({ darkMode, toggleDarkMode }) => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const { data: sports } = useSports();
    
    return (
        <header className="bg-white dark:bg-slate-800 shadow-lg sticky top-0 z-50">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    <Link to="/" className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-gradient-to-br from-green-600 to-amber-500 rounded-lg flex items-center justify-center">
                            <Trophy className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold text-green-600">Sports Portal</span>
                    </Link>
                    
                    <nav className="hidden md:flex items-center space-x-8">
                        <Link to="/" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">
                            Home
                        </Link>
                        <Link to="/live" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors flex items-center">
                            <Play className="w-4 h-4 mr-1" />
                            Live
                        </Link>
                        <Link to="/cricket" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">
                            Cricket
                        </Link>
                        <Link to="/football" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">
                            Football
                        </Link>
                        <Link to="/tennis" className="text-gray-700 dark:text-gray-300 hover:text-green-600 transition-colors">
                            Tennis
                        </Link>
                    </nav>
                    
                    <div className="flex items-center space-x-4">
                        <button className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 transition-colors">
                            <Search className="w-5 h-5" />
                        </button>
                        <button 
                            onClick={toggleDarkMode}
                            className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 transition-colors"
                        >
                            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <button className="p-2 text-gray-600 dark:text-gray-400 hover:text-green-600 transition-colors">
                            <User className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>
        </header>
    );
};

const MatchCard = ({ match }) => {
    const isLive = match.status === 'live';
    const isUpcoming = match.status === 'scheduled';
    
    return (
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 dark:border-slate-700">
            <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                        {match.league?.name}
                    </span>
                    {isLive && (
                        <span className="bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium flex items-center">
                            <div className="w-2 h-2 bg-white rounded-full mr-1 animate-pulse"></div>
                            LIVE
                        </span>
                    )}
                </div>
                
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <div className="text-center">
                            <div className="w-8 h-8 bg-gray-200 dark:bg-slate-600 rounded-full mb-1"></div>
                            <span className="text-sm font-medium">{match.home_team?.short_name}</span>
                        </div>
                    </div>
                    
                    <div className="text-center">
                        {isLive && match.score_summary ? (
                            <div className="text-lg font-bold">
                                {match.score_summary.home || 0} - {match.score_summary.away || 0}
                            </div>
                        ) : isUpcoming ? (
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                                {format(new Date(match.start_time), 'HH:mm')}
                            </div>
                        ) : (
                            <div className="text-sm text-gray-600 dark:text-gray-400">
                                FT
                            </div>
                        )}
                    </div>
                    
                    <div className="flex items-center space-x-3">
                        <div className="text-center">
                            <div className="w-8 h-8 bg-gray-200 dark:bg-slate-600 rounded-full mb-1"></div>
                            <span className="text-sm font-medium">{match.away_team?.short_name}</span>
                        </div>
                    </div>
                </div>
                
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {format(new Date(match.start_time), 'MMM dd, HH:mm')}
                    </div>
                    {match.stream_sources?.length > 0 && (
                        <div className="flex items-center text-green-600">
                            <Tv className="w-4 h-4 mr-1" />
                            Watch Live
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

const HomePage = () => {
    const { data: liveMatches } = useMatches({ status: 'live' });
    const { data: upcomingMatches } = useMatches({ status: 'upcoming' });
    
    return (
        <div className="container mx-auto px-4 py-8">
            {/* Hero Section */}
            <div className="bg-gradient-to-r from-green-600 to-amber-500 rounded-2xl p-8 mb-8 text-white">
                <h1 className="text-4xl font-bold mb-4">Welcome to Sports Portal</h1>
                <p className="text-xl opacity-90">
                    Watch live cricket, football, tennis matches with real-time scores and analysis
                </p>
            </div>
            
            {/* Live Matches */}
            <section className="mb-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
                        <Play className="w-6 h-6 mr-2 text-red-500" />
                        Live Matches
                    </h2>
                    <Link to="/live" className="text-green-600 hover:text-green-700 flex items-center">
                        View All <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {liveMatches?.results?.map(match => (
                        <Link key={match.id} to={`/match/${match.id}`}>
                            <MatchCard match={match} />
                        </Link>
                    ))}
                </div>
                
                {!liveMatches?.results?.length && (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        No live matches at the moment
                    </div>
                )}
            </section>
            
            {/* Upcoming Matches */}
            <section>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
                        <Calendar className="w-6 h-6 mr-2 text-blue-500" />
                        Upcoming Matches
                    </h2>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {upcomingMatches?.results?.slice(0, 6).map(match => (
                        <Link key={match.id} to={`/match/${match.id}`}>
                            <MatchCard match={match} />
                        </Link>
                    ))}
                </div>
            </section>
        </div>
    );
};

const MatchDetail = () => {
    const { matchId } = useParams();
    const { data: match, isLoading } = useMatch(matchId);
    const { lastEvent } = useWebSocket(matchId);
    
    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
                    <div className="h-64 bg-gray-200 rounded mb-4"></div>
                </div>
            </div>
        );
    }
    
    if (!match) {
        return (
            <div className="container mx-auto px-4 py-8 text-center">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Match not found</h1>
            </div>
        );
    }
    
    const activeStream = match.stream_sources?.find(s => s.is_active);
    
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2">
                    {/* Match Header */}
                    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 mb-6">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                                {match.league?.name}
                            </span>
                            {match.status === 'live' && (
                                <span className="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center">
                                    <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
                                    LIVE
                                </span>
                            )}
                        </div>
                        
                        <div className="flex items-center justify-between">
                            <div className="text-center">
                                <div className="w-16 h-16 bg-gray-200 dark:bg-slate-600 rounded-full mb-2 mx-auto"></div>
                                <h3 className="font-semibold">{match.home_team?.name}</h3>
                            </div>
                            
                            <div className="text-center">
                                <div className="text-3xl font-bold mb-2">
                                    {match.score_summary?.home || 0} - {match.score_summary?.away || 0}
                                </div>
                                <div className="text-sm text-gray-600 dark:text-gray-400">
                                    {format(new Date(match.start_time), 'MMM dd, yyyy HH:mm')}
                                </div>
                            </div>
                            
                            <div className="text-center">
                                <div className="w-16 h-16 bg-gray-200 dark:bg-slate-600 rounded-full mb-2 mx-auto"></div>
                                <h3 className="font-semibold">{match.away_team?.name}</h3>
                            </div>
                        </div>
                    </div>
                    
                    {/* Live Stream */}
                    {activeStream && (
                        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 mb-6">
                            <h3 className="text-lg font-semibold mb-4 flex items-center">
                                <Tv className="w-5 h-5 mr-2" />
                                Live Stream
                            </h3>
                            <div className="aspect-video bg-black rounded-lg overflow-hidden">
                                {activeStream.embed_html ? (
                                    <div 
                                        dangerouslySetInnerHTML={{ __html: activeStream.embed_html }}
                                        className="w-full h-full"
                                    />
                                ) : (
                                    <iframe
                                        src={activeStream.url}
                                        className="w-full h-full"
                                        frameBorder="0"
                                        allowFullScreen
                                        sandbox="allow-scripts allow-same-origin allow-presentation"
                                    />
                                )}
                            </div>
                        </div>
                    )}
                </div>
                
                {/* Sidebar */}
                <div>
                    {/* Live Events */}
                    {lastEvent && (
                        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-6 mb-6">
                            <h3 className="text-lg font-semibold mb-4">Latest Event</h3>
                            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                                <div className="font-medium text-green-800 dark:text-green-200">
                                    {lastEvent.event_type}
                                </div>
                                <div className="text-sm text-green-600 dark:text-green-300">
                                    {formatDistanceToNow(new Date(lastEvent.timestamp))} ago
                                </div>
                            </div>
                        </div>
                    )}
                    
                    {/* Ad Placeholder */}
                    <div className="bg-gray-100 dark:bg-slate-700 rounded-lg p-6 mb-6">
                        <div className="text-center text-gray-500 dark:text-gray-400">
                            <div className="w-full h-32 bg-gray-200 dark:bg-slate-600 rounded mb-2"></div>
                            Advertisement
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Main App Component
const App = () => {
    const [darkMode, setDarkMode] = useState(false);
    const queryClient = new QueryClient();
    
    useEffect(() => {
        const savedTheme = localStorage.getItem('darkMode');
        if (savedTheme) {
            setDarkMode(JSON.parse(savedTheme));
        }
    }, []);
    
    useEffect(() => {
        localStorage.setItem('darkMode', JSON.stringify(darkMode));
        if (darkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [darkMode]);
    
    const toggleDarkMode = () => setDarkMode(!darkMode);
    
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <div className="min-h-screen bg-gray-50 dark:bg-slate-900 transition-colors">
                    <Header darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
                    
                    <main>
                        <Routes>
                            <Route path="/" element={<HomePage />} />
                            <Route path="/match/:matchId" element={<MatchDetail />} />
                            <Route path="/live" element={<HomePage />} />
                            <Route path="/cricket" element={<HomePage />} />
                            <Route path="/football" element={<HomePage />} />
                            <Route path="/tennis" element={<HomePage />} />
                        </Routes>
                    </main>
                    
                    <footer className="bg-white dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 py-8 mt-16">
                        <div className="container mx-auto px-4 text-center text-gray-600 dark:text-gray-400">
                            <p>&copy; 2025 Sports Portal. All rights reserved.</p>
                        </div>
                    </footer>
                </div>
            </Router>
        </QueryClientProvider>
    );
};

export default App;