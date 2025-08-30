import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { format, formatDistanceToNow } from 'date-fns';
import { 
    Play, Clock, Tv, Trophy, Users, Calendar,
    ChevronRight, MapPin, Star, Share2, Heart
} from 'lucide-react';

// Reusable UI Components for Sports Portal

export const Button = ({ 
    children, 
    variant = 'primary', 
    size = 'md', 
    className = '', 
    ...props 
}) => {
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    const variants = {
        primary: 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-500',
        secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900 focus:ring-gray-500',
        outline: 'border border-green-600 text-green-600 hover:bg-green-50 focus:ring-green-500',
        ghost: 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:ring-gray-500',
    };
    
    const sizes = {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-sm',
        lg: 'px-6 py-3 text-base',
    };
    
    return (
        <button 
            className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
            {...props}
        >
            {children}
        </button>
    );
};

export const Badge = ({ children, variant = 'default', className = '' }) => {
    const variants = {
        default: 'bg-gray-100 text-gray-800',
        live: 'bg-red-500 text-white animate-pulse',
        upcoming: 'bg-blue-100 text-blue-800',
        finished: 'bg-gray-100 text-gray-600',
        success: 'bg-green-100 text-green-800',
    };
    
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`}>
            {children}
        </span>
    );
};

export const Card = ({ children, className = '', hover = true }) => {
    return (
        <div className={`
            bg-white dark:bg-slate-800 rounded-lg shadow-md border border-gray-200 dark:border-slate-700
            ${hover ? 'hover:shadow-lg transition-shadow' : ''}
            ${className}
        `}>
            {children}
        </div>
    );
};

export const TeamLogo = ({ team, size = 'md' }) => {
    const sizes = {
        sm: 'w-6 h-6',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
        xl: 'w-16 h-16',
    };
    
    const colors = team?.colors || {};
    const primaryColor = colors.primary || '#6B7280';
    
    return (
        <div 
            className={`${sizes[size]} rounded-full flex items-center justify-center text-white font-bold text-xs`}
            style={{ backgroundColor: primaryColor }}
        >
            {team?.short_name?.charAt(0) || '?'}
        </div>
    );
};

export const LiveTicker = ({ matches = [] }) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    
    useEffect(() => {
        if (matches.length > 1) {
            const interval = setInterval(() => {
                setCurrentIndex((prev) => (prev + 1) % matches.length);
            }, 5000);
            
            return () => clearInterval(interval);
        }
    }, [matches.length]);
    
    if (!matches.length) return null;
    
    const currentMatch = matches[currentIndex];
    
    return (
        <div className="bg-green-600 text-white py-2 px-4">
            <div className="container mx-auto">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <Badge variant="live" className="bg-red-500">
                            LIVE
                        </Badge>
                        <span className="font-medium">
                            {currentMatch.home_team?.short_name} vs {currentMatch.away_team?.short_name}
                        </span>
                        <span className="font-bold">
                            {currentMatch.score_summary?.home || 0} - {currentMatch.score_summary?.away || 0}
                        </span>
                    </div>
                    
                    {matches.length > 1 && (
                        <div className="flex space-x-1">
                            {matches.map((_, index) => (
                                <button
                                    key={index}
                                    className={`w-2 h-2 rounded-full transition-colors ${
                                        index === currentIndex ? 'bg-white' : 'bg-white/50'
                                    }`}
                                    onClick={() => setCurrentIndex(index)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export const ScoreEvent = ({ event }) => {
    const getEventIcon = (eventType) => {
        switch (eventType) {
            case 'goal':
                return '⚽';
            case 'wicket':
                return '🏏';
            case 'boundary':
                return '4️⃣';
            case 'card':
                return '🟨';
            default:
                return '📝';
        }
    };
    
    return (
        <div className="flex items-start space-x-3 p-3 border-b border-gray-100 dark:border-slate-700 last:border-b-0">
            <div className="text-lg">{getEventIcon(event.event_type)}</div>
            <div className="flex-1 min-w-0">
                <div className="font-medium text-sm capitalize">
                    {event.event_type.replace('_', ' ')}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                    {event.period && `${event.period} • `}
                    {formatDistanceToNow(new Date(event.timestamp))} ago
                </div>
                {event.payload?.player && (
                    <div className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                        {event.payload.player}
                    </div>
                )}
            </div>
        </div>
    );
};

export const AdSlot = ({ slot, className = '' }) => {
    return (
        <div className={`bg-gray-100 dark:bg-slate-700 rounded-lg p-4 text-center ${className}`}>
            <div className="text-gray-500 dark:text-gray-400 text-sm mb-2">
                Advertisement
            </div>
            <div className="w-full h-32 bg-gray-200 dark:bg-slate-600 rounded flex items-center justify-center">
                <span className="text-gray-400 text-xs">Ad Space - {slot}</span>
            </div>
        </div>
    );
};

export const LoadingSpinner = ({ size = 'md' }) => {
    const sizes = {
        sm: 'w-4 h-4',
        md: 'w-8 h-8',
        lg: 'w-12 h-12',
    };
    
    return (
        <div className={`${sizes[size]} border-2 border-gray-300 border-t-green-600 rounded-full animate-spin`}></div>
    );
};

export const EmptyState = ({ 
    icon: Icon = Trophy, 
    title = 'No data available', 
    description = 'Check back later for updates',
    action = null 
}) => {
    return (
        <div className="text-center py-12">
            <Icon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {title}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
                {description}
            </p>
            {action}
        </div>
    );
};

export const MatchStatus = ({ status, startTime }) => {
    const getStatusDisplay = () => {
        switch (status) {
            case 'live':
                return { text: 'LIVE', color: 'bg-red-500 text-white', pulse: true };
            case 'scheduled':
                return { 
                    text: format(new Date(startTime), 'HH:mm'), 
                    color: 'bg-blue-100 text-blue-800',
                    pulse: false 
                };
            case 'finished':
                return { text: 'FT', color: 'bg-gray-100 text-gray-600', pulse: false };
            case 'postponed':
                return { text: 'Postponed', color: 'bg-yellow-100 text-yellow-800', pulse: false };
            case 'cancelled':
                return { text: 'Cancelled', color: 'bg-red-100 text-red-800', pulse: false };
            default:
                return { text: status, color: 'bg-gray-100 text-gray-600', pulse: false };
        }
    };
    
    const statusDisplay = getStatusDisplay();
    
    return (
        <span className={`
            inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
            ${statusDisplay.color}
            ${statusDisplay.pulse ? 'animate-pulse' : ''}
        `}>
            {statusDisplay.pulse && (
                <div className="w-2 h-2 bg-white rounded-full mr-1 animate-pulse"></div>
            )}
            {statusDisplay.text}
        </span>
    );
};

export const StreamPlayer = ({ stream, className = '' }) => {
    if (!stream) {
        return (
            <div className={`aspect-video bg-gray-900 rounded-lg flex items-center justify-center ${className}`}>
                <div className="text-white text-center">
                    <Tv className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No stream available</p>
                </div>
            </div>
        );
    }
    
    return (
        <div className={`aspect-video bg-black rounded-lg overflow-hidden ${className}`}>
            {stream.embed_html ? (
                <div 
                    dangerouslySetInnerHTML={{ __html: stream.embed_html }}
                    className="w-full h-full"
                />
            ) : (
                <iframe
                    src={stream.url}
                    className="w-full h-full"
                    frameBorder="0"
                    allowFullScreen
                    sandbox="allow-scripts allow-same-origin allow-presentation"
                    title="Live Stream"
                />
            )}
        </div>
    );
};

export const NewsCard = ({ article, featured = false }) => {
    return (
        <Card className={featured ? 'md:col-span-2' : ''}>
            <div className={`${featured ? 'md:flex' : ''}`}>
                {article.hero_image && (
                    <div className={`${featured ? 'md:w-1/2' : 'w-full h-48'} bg-gray-200 dark:bg-slate-600`}>
                        <img 
                            src={article.hero_image} 
                            alt={article.title}
                            className="w-full h-full object-cover"
                        />
                    </div>
                )}
                
                <div className={`p-4 ${featured ? 'md:w-1/2' : ''}`}>
                    <div className="flex items-center space-x-2 mb-2">
                        {article.tags?.slice(0, 2).map(tag => (
                            <Badge key={tag} variant="default" className="text-xs">
                                {tag}
                            </Badge>
                        ))}
                    </div>
                    
                    <h3 className={`font-bold mb-2 ${featured ? 'text-xl' : 'text-lg'}`}>
                        <Link 
                            to={`/news/${article.slug}`}
                            className="hover:text-green-600 transition-colors"
                        >
                            {article.title}
                        </Link>
                    </h3>
                    
                    {article.excerpt && (
                        <p className="text-gray-600 dark:text-gray-400 text-sm mb-3 line-clamp-3">
                            {article.excerpt}
                        </p>
                    )}
                    
                    <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                        <span>By {article.author}</span>
                        <span>{formatDistanceToNow(new Date(article.published_at))} ago</span>
                    </div>
                </div>
            </div>
        </Card>
    );
};

export default {
    Button,
    Badge,
    Card,
    TeamLogo,
    LiveTicker,
    ScoreEvent,
    AdSlot,
    LoadingSpinner,
    EmptyState,
    MatchStatus,
    StreamPlayer,
    NewsCard
};