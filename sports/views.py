from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes, inline_serializer
import logging

from .models import (
    Sport, League, Team, Match, StreamSource, ScoreEvent,
    Article, AdPlacement, AdCreative, AuditLog, IPTVChannel
)

User = get_user_model()

logger = logging.getLogger(__name__)


# ─── Serializers ─────────────────────────────────────────────────────────────

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


class IPTVChannelSerializer(serializers.ModelSerializer):
    attribution = serializers.SerializerMethodField()

    class Meta:
        model = IPTVChannel
        fields = [
            'id', 'name', 'slug', 'stream_url', 'logo', 'category',
            'country', 'country_code', 'language', 'is_featured',
            'source_name', 'source_url', 'attribution'
        ]

    def get_attribution(self, obj):
        return f"Channel metadata from {obj.source_name}. Streams play from their original public URLs."


# ─── ViewSets ────────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(tags=['sports'], summary='List all active sports'),
    retrieve=extend_schema(tags=['sports'], summary='Get a single sport'),
)
class SportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sport.objects.filter(is_active=True)
    serializer_class = SportSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema_view(
    list=extend_schema(tags=['leagues'], summary='List all leagues', parameters=[
        OpenApiParameter('sport', OpenApiTypes.STR, description='Filter by sport slug e.g. cricket')
    ]),
    retrieve=extend_schema(tags=['leagues'], summary='Get a single league'),
)
class LeagueViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = League.objects.filter(is_active=True).select_related('sport')
        sport = self.request.query_params.get('sport')
        if sport:
            queryset = queryset.filter(sport__slug=sport)
        return queryset


@extend_schema_view(
    list=extend_schema(tags=['teams'], summary='List all teams', parameters=[
        OpenApiParameter('league', OpenApiTypes.STR, description='Filter by league slug e.g. ipl')
    ]),
    retrieve=extend_schema(tags=['teams'], summary='Get a single team'),
)
class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Team.objects.filter(is_active=True).select_related('league__sport')
        league = self.request.query_params.get('league')
        if league:
            queryset = queryset.filter(league__slug=league)
        return queryset


@extend_schema_view(
    list=extend_schema(tags=['matches'], summary='List matches', parameters=[
        OpenApiParameter('status', OpenApiTypes.STR, description='Filter by status: live, upcoming, finished'),
        OpenApiParameter('sport', OpenApiTypes.STR, description='Filter by sport slug'),
        OpenApiParameter('league', OpenApiTypes.STR, description='Filter by league slug'),
    ]),
    retrieve=extend_schema(tags=['matches'], summary='Get a single match'),
)
class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Match.objects.select_related(
            'home_team__league__sport', 'away_team__league__sport', 'league__sport'
        ).prefetch_related(
            Prefetch('stream_sources', queryset=StreamSource.objects.filter(is_active=True))
        )

        status_filter = self.request.query_params.get('status')
        if status_filter == 'live':
            queryset = queryset.filter(status='live')
        elif status_filter == 'upcoming':
            queryset = queryset.filter(status='scheduled', start_time__gt=timezone.now())
        elif status_filter == 'finished':
            queryset = queryset.filter(status='finished')

        sport = self.request.query_params.get('sport')
        if sport:
            queryset = queryset.filter(league__sport__slug=sport)

        league = self.request.query_params.get('league')
        if league:
            queryset = queryset.filter(league__slug=league)

        return queryset.order_by('-start_time')

    @extend_schema(tags=['matches'], summary='Get best active stream for a match',
                   description='Returns the highest-priority active stream. Unauthenticated users only see public streams (requires_auth=False).',
                   responses={200: StreamSourceSerializer})
    @action(detail=True, methods=['get'])
    def streams(self, request, pk=None):
        """Get active streams for a match"""
        match = self.get_object()
        streams = match.stream_sources.filter(is_active=True)

        if not request.user.is_authenticated:
            streams = streams.filter(requires_auth=False)

        if streams.exists():
            best_stream = streams.order_by('-priority').first()
            return Response(StreamSourceSerializer(best_stream).data)

        return Response(
            {'detail': 'No active streams available'},
            status=status.HTTP_404_NOT_FOUND
        )

    @extend_schema(tags=['matches'], summary='List score events for a match',
                   description='Returns the last 50 score events (goals, wickets, cards, etc.) for this match.',
                   responses={200: ScoreEventSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get score events for a match"""
        match = self.get_object()
        events = match.score_events.all()[:50]
        return Response(ScoreEventSerializer(events, many=True).data)


@extend_schema_view(
    list=extend_schema(tags=['articles'], summary='List published news articles'),
    retrieve=extend_schema(tags=['articles'], summary='Get article by slug'),
)
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        return Article.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author').order_by('-published_at')


@extend_schema_view(
    list=extend_schema(tags=['iptv'], summary='List public IPTV channels', parameters=[
        OpenApiParameter('q', OpenApiTypes.STR, description='Search by channel name'),
        OpenApiParameter('category', OpenApiTypes.STR, description='Filter by group/category, e.g. Sports'),
        OpenApiParameter('country', OpenApiTypes.STR, description='Filter by country code or country name'),
        OpenApiParameter('language', OpenApiTypes.STR, description='Filter by language'),
        OpenApiParameter('featured', OpenApiTypes.BOOL, description='Only featured channels'),
    ]),
    retrieve=extend_schema(tags=['iptv'], summary='Get a single IPTV channel'),
)
class IPTVChannelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IPTVChannelSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = IPTVChannel.objects.filter(is_active=True)

        q = self.request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(name__icontains=q)

        category = self.request.query_params.get('category', '').strip()
        if category:
            queryset = queryset.filter(category__iexact=category)

        country = self.request.query_params.get('country', '').strip()
        if country:
            queryset = queryset.filter(
                Q(country_code__iexact=country) | Q(country__icontains=country)
            )

        language = self.request.query_params.get('language', '').strip()
        if language:
            queryset = queryset.filter(language__icontains=language)

        featured = self.request.query_params.get('featured')
        if featured in ['1', 'true', 'True']:
            queryset = queryset.filter(is_featured=True)

        return queryset.order_by('-is_featured', 'name')


# ─── Function-based API views ────────────────────────────────────────────────

@extend_schema(tags=['matches'], responses=MatchSerializer(many=True), summary="List all currently live matches")
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def live_matches(request):
    matches = Match.objects.filter(status='live').select_related(
        'home_team', 'away_team', 'league__sport'
    )[:10]
    return Response(MatchSerializer(matches, many=True).data)


@extend_schema(tags=['matches'], responses=MatchSerializer(many=True), summary="List upcoming scheduled matches")
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def upcoming_matches(request):
    matches = Match.objects.filter(
        status='scheduled',
        start_time__gt=timezone.now()
    ).select_related('home_team', 'away_team', 'league__sport')[:20]
    return Response(MatchSerializer(matches, many=True).data)


@extend_schema(
    tags=['matches'],
    parameters=[OpenApiParameter('league', OpenApiTypes.STR, description='League slug', required=True)],
    responses={200: inline_serializer('StandingsResponse', fields={
        'league': LeagueSerializer(),
        'standings': serializers.ListField(child=inline_serializer('StandingRow', fields={
            'team': TeamSerializer(),
            'matches_played': serializers.IntegerField(),
            'wins': serializers.IntegerField(),
            'losses': serializers.IntegerField(),
            'points': serializers.IntegerField(),
        }))
    })},
    summary="Get league standings"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def standings(request):
    league_slug = request.GET.get('league')
    if not league_slug:
        return Response(
            {'error': 'League parameter required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        league = League.objects.get(slug=league_slug)
        teams = league.teams.filter(is_active=True)
        standings_data = [
            {
                'team': TeamSerializer(team).data,
                'matches_played': 0,
                'wins': 0,
                'losses': 0,
                'points': 0
            }
            for team in teams
        ]
        return Response({
            'league': LeagueSerializer(league).data,
            'standings': standings_data
        })

    except League.DoesNotExist:
        return Response(
            {'error': 'League not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@extend_schema(tags=['matches'], request=ScoreEventSerializer, responses=ScoreEventSerializer,
               summary="Create a score event and broadcast via WebSocket",
               description="Creates a score event (goal, wicket, card, etc.) for a live match and immediately broadcasts it to all WebSocket clients watching that match. Requires editor role or above.")
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_score_event(request, match_id):
    """Create a new score event and broadcast via WebSocket"""
    if request.user.role not in ['editor', 'streamer_admin', 'sysadmin']:
        return Response(
            {'error': 'Insufficient permissions'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        match = Match.objects.get(id=match_id)
        event = ScoreEvent.objects.create(
            match=match,
            event_type=request.data.get('event_type'),
            period=request.data.get('period', ''),
            payload=request.data.get('payload', {})
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

        # Audit log
        AuditLog.objects.create(
            actor=request.user,
            action='create_score_event',
            object_type='ScoreEvent',
            object_id=str(event.id),
            after_data=ScoreEventSerializer(event).data,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response(
            ScoreEventSerializer(event).data,
            status=status.HTTP_201_CREATED
        )

    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating score event: {e}")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['ads'],
    parameters=[
        OpenApiParameter('slot', OpenApiTypes.STR, description='Ad slot key e.g. header_banner'),
        OpenApiParameter('device', OpenApiTypes.STR, description='Device type: all/desktop/mobile/tablet'),
    ],
    responses={200: inline_serializer('AdListResponse', fields={
        'ads': serializers.ListField(child=inline_serializer('AdItem', fields={
            'id': serializers.IntegerField(),
            'name': serializers.CharField(),
            'html': serializers.CharField(),
            'capping_rules': serializers.JSONField(),
        }))
    })},
    summary="Get active ad creatives for a slot"
)
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
        now = timezone.now()
        creatives = placement.creatives.filter(
            is_active=True,
            start_at__lte=now
        ).filter(
            Q(end_at__isnull=True) | Q(end_at__gt=now)
        )

        ads_data = [
            {
                'id': c.id,
                'name': c.name,
                'html': c.html_snippet,
                'capping_rules': c.capping_rules
            }
            for c in creatives
        ]
        return Response({'ads': ads_data})

    except AdPlacement.DoesNotExist:
        return Response({'ads': []})


@extend_schema(
    tags=['search'],
    parameters=[OpenApiParameter('q', OpenApiTypes.STR, description='Search query (min 2 chars)', required=True)],
    responses={200: inline_serializer('SearchResponse', fields={
        'matches': MatchSerializer(many=True),
        'articles': ArticleSerializer(many=True),
        'teams': TeamSerializer(many=True),
    })},
    summary="Search matches, articles, and teams"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search(request):
    """Global search across matches, articles, and teams"""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return Response({'matches': [], 'articles': [], 'teams': []})

    matches = Match.objects.filter(
        Q(home_team__name__icontains=q) |
        Q(away_team__name__icontains=q) |
        Q(league__name__icontains=q)
    ).select_related('home_team', 'away_team', 'league__sport')[:8]

    articles = Article.objects.filter(
        status='published',
        published_at__lte=timezone.now()
    ).filter(
        Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q)
    ).select_related('author')[:8]

    teams = Team.objects.filter(
        Q(name__icontains=q) | Q(short_name__icontains=q)
    ).select_related('league__sport')[:5]

    return Response({
        'matches': MatchSerializer(matches, many=True).data,
        'articles': ArticleSerializer(articles, many=True).data,
        'teams': TeamSerializer(teams, many=True).data,
    })


@extend_schema(
    tags=['auth'],
    request=inline_serializer('RegisterRequest', fields={
        'username': serializers.CharField(),
        'email': serializers.EmailField(),
        'password': serializers.CharField(),
    }),
    responses={201: inline_serializer('RegisterResponse', fields={
        'message': serializers.CharField(),
        'username': serializers.CharField(),
    })},
    summary="Register a new user account"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """Register a new user account"""
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not username or not email or not password:
        return Response(
            {'error': 'username, email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if len(password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role='registered'
    )
    return Response(
        {'message': 'Account created', 'username': user.username},
        status=status.HTTP_201_CREATED
    )


@extend_schema(
    methods=['GET'],
    tags=['auth'],
    responses={200: inline_serializer('UserProfileResponse', fields={
        'id': serializers.IntegerField(),
        'username': serializers.CharField(),
        'email': serializers.EmailField(),
        'role': serializers.CharField(),
        'is_premium': serializers.BooleanField(),
        'favorite_teams': serializers.JSONField(),
        'notification_prefs': serializers.JSONField(),
        'date_joined': serializers.DateTimeField(),
    })},
    summary="Get the authenticated user's profile"
)
@extend_schema(
    methods=['PATCH'],
    tags=['auth'],
    request=inline_serializer('UserProfileUpdate', fields={
        'favorite_teams': serializers.JSONField(required=False),
        'notification_prefs': serializers.JSONField(required=False),
    }),
    responses={200: inline_serializer('UserProfileUpdateResponse', fields={
        'message': serializers.CharField(),
    })},
    summary="Update the authenticated user's profile"
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update the authenticated user's profile"""
    user = request.user

    if request.method == 'GET':
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_premium': user.is_premium,
            'favorite_teams': user.favorite_teams,
            'notification_prefs': user.notification_prefs,
            'date_joined': user.date_joined,
        })

    # PATCH
    allowed_fields = ['favorite_teams', 'notification_prefs']
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    user.save(update_fields=allowed_fields)
    return Response({'message': 'Profile updated'})


def index(request):
    """Serve the React frontend SPA"""
    return render(request, 'index.html')
