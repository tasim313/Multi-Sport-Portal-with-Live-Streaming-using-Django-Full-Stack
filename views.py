from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Prefetch
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
import logging

from .models import (
    Sport, League, Team, Match, StreamSource, ScoreEvent, 
    Article, AdPlacement, AdCreative, User, AuditLog
)

logger = logging.getLogger(__name__)

# Serializers (inline for simplicity)
from rest_framework import serializers

class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ['id', 'name', 'slug', 'icon', 'is_active']

class LeagueSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    
    class Meta:
        model = League
        fields = ['id', 'name', 'slug', 'season', 'country', 'logo', 'sport']

class TeamSerializer(serializers.ModelSerializer):
    league = LeagueSerializer(read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'slug', 'logo', 'colors', 'country', 'league']

class StreamSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreamSource
        fields = [
            'id', 'provider', 'url', 'embed_html', 'is_iframe', 
            'requires_auth', 'priority', 'is_active'
        ]

class MatchSerializer(serializers.ModelSerializer):
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)
    league = LeagueSerializer(read_only=True)
    stream_sources = StreamSourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team', 'league', 'venue',
            'start_time', 'end_time', 'status', 'score_summary',
            'metadata', 'stream_sources'
        ]

class ScoreEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreEvent
        fields = ['id', 'timestamp', 'period', 'event_type', 'payload']

class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'body', 'excerpt', 'author',
            'tags', 'hero_image', 'published_at', 'meta_description'
        ]

# ViewSets
class SportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sport.objects.filter(is_active=True)
    serializer_class = SportSerializer
    permission_classes = [permissions.AllowAny]

class LeagueViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = League.objects.filter(is_active=True).select_related('sport')
        sport = self.request.query_params.get('sport')
        if sport:
            queryset = queryset.filter(sport__slug=sport)
        return queryset

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Team.objects.filter(is_active=True).select_related('league__sport')
        league = self.request.query_params.get('league')
        if league:
            queryset = queryset.filter(league__slug=league)
        return queryset

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Match.objects.select_related(
            'home_team__league__sport', 'away_team__league__sport', 'league__sport'
        ).prefetch_related(
            Prefetch('stream_sources', queryset=StreamSource.objects.filter(is_active=True))
        )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            if status_filter == 'live':
                queryset = queryset.filter(status='live')
            elif status_filter == 'upcoming':
                queryset = queryset.filter(
                    status='scheduled',
                    start_time__gt=timezone.now()
                )
            elif status_filter == 'finished':
                queryset = queryset.filter(status='finished')
        
        # Filter by sport
        sport = self.request.query_params.get('sport')
        if sport:
            queryset = queryset.filter(league__sport__slug=sport)
        
        # Filter by league
        league = self.request.query_params.get('league')
        if league:
            queryset = queryset.filter(league__slug=league)
        
        return queryset.order_by('-start_time')
    
    @action(detail=True, methods=['get'])
    def streams(self, request, pk=None):
        """Get active streams for a match"""
        match = self.get_object()
        user = request.user
        
        # Filter streams based on user role and geo (simplified)
        streams = match.stream_sources.filter(is_active=True)
        
        # Basic auth filtering
        if not user.is_authenticated:
            streams = streams.filter(requires_auth=False)
        
        # Return best stream by priority
        if streams.exists():
            best_stream = streams.order_by('-priority').first()
            serializer = StreamSourceSerializer(best_stream)
            return Response(serializer.data)
        
        return Response({'detail': 'No active streams available'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get score events for a match"""
        match = self.get_object()
        events = match.score_events.all()[:50]  # Latest 50 events
        serializer = ScoreEventSerializer(events, many=True)
        return Response(serializer.data)

class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Article.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author').order_by('-published_at')

# API Views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def live_matches(request):
    """Get currently live matches"""
    matches = Match.objects.filter(status='live').select_related(
        'home_team', 'away_team', 'league__sport'
    )[:10]
    
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def upcoming_matches(request):
    """Get upcoming matches"""
    matches = Match.objects.filter(
        status='scheduled',
        start_time__gt=timezone.now()
    ).select_related('home_team', 'away_team', 'league__sport')[:20]
    
    serializer = MatchSerializer(matches, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def standings(request):
    """Get league standings (simplified)"""
    league_slug = request.GET.get('league')
    if not league_slug:
        return Response({'error': 'League parameter required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        league = League.objects.get(slug=league_slug)
        teams = league.teams.filter(is_active=True)
        
        # Simplified standings - in real app, calculate from match results
        standings_data = []
        for team in teams:
            standings_data.append({
                'team': TeamSerializer(team).data,
                'matches_played': 0,
                'wins': 0,
                'losses': 0,
                'points': 0
            })
        
        return Response({
            'league': LeagueSerializer(league).data,
            'standings': standings_data
        })
    
    except League.DoesNotExist:
        return Response({'error': 'League not found'}, 
                       status=status.HTTP_404_NOT_FOUND)

# WebSocket Consumer for Real-time Updates
class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.match_group_name = f'match_{self.match_id}'
        
        # Join match group
        await self.channel_layer.group_add(
            self.match_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send current match data
        match_data = await self.get_match_data()
        await self.send(text_data=json.dumps({
            'type': 'match_data',
            'data': match_data
        }))
    
    async def disconnect(self, close_code):
        # Leave match group
        await self.channel_layer.group_discard(
            self.match_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        # Handle incoming WebSocket messages (e.g., subscription preferences)
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        
        except json.JSONDecodeError:
            pass
    
    # Receive message from match group
    async def score_update(self, event):
        # Send score update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'data': event['data']
        }))
    
    async def match_status_update(self, event):
        # Send match status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_match_data(self):
        try:
            match = Match.objects.select_related(
                'home_team', 'away_team', 'league'
            ).get(id=self.match_id)
            
            return MatchSerializer(match).data
        except Match.DoesNotExist:
            return None

# Admin Views (simplified)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_score_event(request, match_id):
    """Create a new score event (admin only)"""
    if not request.user.role in ['editor', 'streamer_admin', 'sysadmin']:
        return Response({'error': 'Insufficient permissions'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        match = Match.objects.get(id=match_id)
        
        event_data = request.data
        event = ScoreEvent.objects.create(
            match=match,
            event_type=event_data.get('event_type'),
            period=event_data.get('period', ''),
            payload=event_data.get('payload', {})
        )
        
        # Broadcast to WebSocket group
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {
                'type': 'score_update',
                'data': ScoreEventSerializer(event).data
            }
        )
        
        # Log the action
        AuditLog.objects.create(
            actor=request.user,
            action='create_score_event',
            object_type='ScoreEvent',
            object_id=str(event.id),
            after_data=ScoreEventSerializer(event).data,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(ScoreEventSerializer(event).data, 
                       status=status.HTTP_201_CREATED)
    
    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating score event: {str(e)}")
        return Response({'error': 'Internal server error'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Ad serving endpoint
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ads(request):
    """Get ads for a specific slot"""
    slot_key = request.GET.get('slot')
    device = request.GET.get('device', 'all')
    
    if not slot_key:
        return Response({'ads': []})
    
    try:
        placement = AdPlacement.objects.get(
            slot_key=slot_key,
            is_active=True,
            device_target__in=[device, 'all']
        )
        
        # Get active creatives
        now = timezone.now()
        creatives = placement.creatives.filter(
            is_active=True,
            start_at__lte=now
        ).filter(
            Q(end_at__isnull=True) | Q(end_at__gt=now)
        )
        
        ads_data = []
        for creative in creatives:
            ads_data.append({
                'id': creative.id,
                'name': creative.name,
                'html': creative.html_snippet,
                'capping_rules': creative.capping_rules
            })
        
        return Response({'ads': ads_data})
    
    except AdPlacement.DoesNotExist:
        return Response({'ads': []})

# Frontend view (serves React app)
def index(request):
    """Serve the React frontend"""
    return render(request, 'index.html')