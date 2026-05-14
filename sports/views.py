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
    Article, AdPlacement, AdCreative, AuditLog, IPTVChannel,
    EPGProgram, LiveCommentary, PlayerProfile, LeagueTable, UserFavorite
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


class PlayerProfileSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)

    class Meta:
        model = PlayerProfile
        fields = [
            'id', 'name', 'slug', 'team', 'nationality', 'position',
            'jersey_number', 'date_of_birth', 'photo', 'stats', 'bio', 'is_active'
        ]


class LeagueTableSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)

    class Meta:
        model = LeagueTable
        fields = [
            'id', 'team', 'season', 'position', 'played', 'won', 'drawn',
            'lost', 'goals_for', 'goals_against', 'goal_difference', 'points', 'form'
        ]


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
        fields = [
            'id', 'timestamp', 'period', 'minute', 'event_type',
            'payload', 'player_name', 'team_side'
        ]


class LiveCommentarySerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveCommentary
        fields = [
            'id', 'minute', 'period', 'rewritten_text', 'is_key_event',
            'language', 'source', 'created_at'
        ]


class ArticleSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    sport = SportSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'body', 'excerpt', 'author', 'sport',
            'tags', 'hero_image', 'category', 'published_at', 'meta_description',
            'views_count'
        ]


class IPTVChannelSerializer(serializers.ModelSerializer):
    attribution = serializers.SerializerMethodField()
    current_program = serializers.SerializerMethodField()

    class Meta:
        model = IPTVChannel
        fields = [
            'id', 'name', 'slug', 'stream_url', 'logo', 'category',
            'country', 'country_code', 'language', 'is_featured', 'is_working',
            'source_name', 'source_url', 'attribution', 'current_program'
        ]

    def get_attribution(self, obj):
        return f"Channel metadata from {obj.source_name}. Streams play from their original public URLs."

    def get_current_program(self, obj):
        now = timezone.now()
        program = obj.epg_programs.filter(
            start_time__lte=now, end_time__gte=now
        ).first()
        if program:
            return {
                'title': program.title,
                'description': program.description,
                'end_time': program.end_time.isoformat(),
            }
        return None


class EPGProgramSerializer(serializers.ModelSerializer):
    is_live = serializers.BooleanField(read_only=True)

    class Meta:
        model = EPGProgram
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time',
            'category', 'language', 'icon', 'is_live'
        ]


class UserFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorite
        fields = ['id', 'item_type', 'item_id', 'item_name', 'created_at']
        read_only_fields = ['created_at']


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
    list=extend_schema(tags=['players'], summary='List players', parameters=[
        OpenApiParameter('team', OpenApiTypes.INT, description='Filter by team ID'),
    ]),
    retrieve=extend_schema(tags=['players'], summary='Get a player profile'),
)
class PlayerProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlayerProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = PlayerProfile.objects.filter(is_active=True).select_related('team__league__sport')
        team_id = self.request.query_params.get('team')
        if team_id:
            queryset = queryset.filter(team_id=team_id)
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
                   responses={200: StreamSourceSerializer})
    @action(detail=True, methods=['get'])
    def streams(self, request, pk=None):
        match = self.get_object()
        streams = match.stream_sources.filter(is_active=True)
        if not request.user.is_authenticated:
            streams = streams.filter(requires_auth=False)
        if streams.exists():
            best_stream = streams.order_by('-priority').first()
            return Response(StreamSourceSerializer(best_stream).data)
        return Response({'detail': 'No active streams available'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(tags=['matches'], summary='List score events for a match',
                   responses={200: ScoreEventSerializer(many=True)})
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        match = self.get_object()
        events = match.score_events.all()[:50]
        return Response(ScoreEventSerializer(events, many=True).data)

    @extend_schema(tags=['matches'], summary='Get AI-rewritten live commentary',
                   responses={200: LiveCommentarySerializer(many=True)})
    @action(detail=True, methods=['get'])
    def commentary(self, request, pk=None):
        match = self.get_object()
        limit = min(int(request.query_params.get('limit', 20)), 100)
        qs = match.commentary.filter(language='en').order_by('-created_at')[:limit]
        return Response(LiveCommentarySerializer(qs, many=True).data)

    @extend_schema(tags=['matches'], summary='Get AI match summary from metadata',
                   responses={200: inline_serializer('SummaryResponse', fields={
                       'summary': serializers.CharField()
                   })})
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        match = self.get_object()
        summary = match.metadata.get('ai_summary', '')
        if not summary:
            return Response({'summary': None}, status=status.HTTP_404_NOT_FOUND)
        return Response({'summary': summary})


@extend_schema_view(
    list=extend_schema(tags=['articles'], summary='List published news articles', parameters=[
        OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category: news, preview, review, highlight, transfer'),
        OpenApiParameter('sport', OpenApiTypes.STR, description='Filter by sport slug'),
    ]),
    retrieve=extend_schema(tags=['articles'], summary='Get article by slug'),
)
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ArticleSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Article.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'sport').order_by('-published_at')

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        sport = self.request.query_params.get('sport')
        if sport:
            queryset = queryset.filter(sport__slug=sport)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        Article.objects.filter(pk=instance.pk).update(views_count=instance.views_count + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['iptv'], summary='List public IPTV channels', parameters=[
        OpenApiParameter('q', OpenApiTypes.STR, description='Search by channel name'),
        OpenApiParameter('category', OpenApiTypes.STR, description='Filter by category: Sports/News/Entertainment/Movies/Kids/Music'),
        OpenApiParameter('country', OpenApiTypes.STR, description='Filter by country code'),
        OpenApiParameter('language', OpenApiTypes.STR, description='Filter by language'),
        OpenApiParameter('featured', OpenApiTypes.BOOL, description='Only featured channels'),
        OpenApiParameter('working', OpenApiTypes.BOOL, description='Only working streams (default true)'),
    ]),
    retrieve=extend_schema(tags=['iptv'], summary='Get a single IPTV channel'),
)
class IPTVChannelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IPTVChannelSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = IPTVChannel.objects.filter(is_active=True)

        # Default: only show working streams
        working = self.request.query_params.get('working', '1')
        if working not in ['0', 'false', 'False']:
            queryset = queryset.filter(is_working=True)

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

    @extend_schema(tags=['iptv'], summary='Get EPG programs for a channel')
    @action(detail=True, methods=['get'])
    def epg(self, request, slug=None):
        channel = self.get_object()
        now = timezone.now()
        programs = channel.epg_programs.filter(
            end_time__gte=now
        ).order_by('start_time')[:20]
        return Response(EPGProgramSerializer(programs, many=True).data)


@extend_schema_view(
    list=extend_schema(tags=['standings'], summary='Get league table', parameters=[
        OpenApiParameter('league', OpenApiTypes.INT, description='League ID', required=True),
        OpenApiParameter('season', OpenApiTypes.STR, description='Season e.g. 2024-2025'),
    ]),
)
class LeagueTableViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeagueTableSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = LeagueTable.objects.select_related('team', 'league')
        league_id = self.request.query_params.get('league')
        if league_id:
            queryset = queryset.filter(league_id=league_id)
        season = self.request.query_params.get('season')
        if season:
            queryset = queryset.filter(season=season)
        return queryset.order_by('position')


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
    summary="Get league standings (legacy endpoint)"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def standings(request):
    league_slug = request.GET.get('league')
    if not league_slug:
        return Response({'error': 'League parameter required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        league = League.objects.get(slug=league_slug)
        table_rows = LeagueTable.objects.filter(
            league=league
        ).select_related('team').order_by('position')

        if table_rows.exists():
            return Response({
                'league': LeagueSerializer(league).data,
                'standings': LeagueTableSerializer(table_rows, many=True).data
            })

        # Fallback: return team list with zero stats
        teams = league.teams.filter(is_active=True)
        standings_data = [
            {'team': TeamSerializer(team).data, 'matches_played': 0, 'wins': 0, 'losses': 0, 'points': 0}
            for team in teams
        ]
        return Response({'league': LeagueSerializer(league).data, 'standings': standings_data})

    except League.DoesNotExist:
        return Response({'error': 'League not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=['matches'], request=ScoreEventSerializer, responses=ScoreEventSerializer,
    summary="Create a score event and broadcast via WebSocket"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_score_event(request, match_id):
    if request.user.role not in ['editor', 'streamer_admin', 'sysadmin']:
        return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)

    try:
        match = Match.objects.get(id=match_id)
        event = ScoreEvent.objects.create(
            match=match,
            event_type=request.data.get('event_type'),
            period=request.data.get('period', ''),
            minute=request.data.get('minute'),
            player_name=request.data.get('player_name', ''),
            team_side=request.data.get('team_side', ''),
            payload=request.data.get('payload', {})
        )

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {'type': 'score_update', 'data': ScoreEventSerializer(event).data}
        )

        # Queue AI commentary
        from ai_commentary.tasks import rewrite_commentary_for_event
        rewrite_commentary_for_event.delay(event.id)

        AuditLog.objects.create(
            actor=request.user, action='create_score_event',
            object_type='ScoreEvent', object_id=str(event.id),
            after_data=ScoreEventSerializer(event).data,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        return Response(ScoreEventSerializer(event).data, status=status.HTTP_201_CREATED)

    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error creating score event: {e}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['commentary'], request=inline_serializer('CommentaryRequest', fields={
        'minute': serializers.IntegerField(required=False),
        'period': serializers.CharField(required=False),
        'text': serializers.CharField(),
    }),
    responses={201: LiveCommentarySerializer},
    summary="Add manual commentary for a live match (auto AI-rewritten)"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_commentary(request, match_id):
    if request.user.role not in ['editor', 'streamer_admin', 'sysadmin']:
        return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)

    try:
        match = Match.objects.get(id=match_id)
        original_text = request.data.get('text', '').strip()
        if not original_text:
            return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)

        from ai_commentary.rewriter import rewrite_commentary
        sport = match.league.sport.name.lower()
        rewritten = rewrite_commentary(original_text, sport=sport)

        commentary = LiveCommentary.objects.create(
            match=match,
            minute=request.data.get('minute'),
            period=request.data.get('period', ''),
            original_text=original_text,
            rewritten_text=rewritten,
            source='manual',
            language='en',
        )

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {
                'type': 'commentary_update',
                'data': {
                    'minute': commentary.minute,
                    'period': commentary.period,
                    'text': commentary.rewritten_text,
                    'is_key': commentary.is_key_event,
                }
            }
        )

        return Response(LiveCommentarySerializer(commentary).data, status=status.HTTP_201_CREATED)

    except Match.DoesNotExist:
        return Response({'error': 'Match not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=['ads'],
    parameters=[
        OpenApiParameter('slot', OpenApiTypes.STR, description='Ad slot key e.g. header_banner'),
        OpenApiParameter('device', OpenApiTypes.STR, description='Device type: all/desktop/mobile/tablet'),
    ],
    summary="Get active ad creatives for a slot"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_ads(request):
    slot_key = request.GET.get('slot')
    device = request.GET.get('device', 'all')

    if not slot_key:
        return Response({'ads': []})

    try:
        placement = AdPlacement.objects.get(slot_key=slot_key, is_active=True)
        now = timezone.now()
        creatives = placement.creatives.filter(
            is_active=True, start_at__lte=now
        ).filter(Q(end_at__isnull=True) | Q(end_at__gt=now))

        ads_data = [
            {'id': c.id, 'name': c.name, 'html': c.html_snippet,
             'image_url': c.image_url, 'click_url': c.click_url,
             'capping_rules': c.capping_rules}
            for c in creatives
        ]
        return Response({'ads': ads_data, 'rotation_interval': placement.rotation_interval})

    except AdPlacement.DoesNotExist:
        return Response({'ads': []})


@extend_schema(
    tags=['search'],
    parameters=[OpenApiParameter('q', OpenApiTypes.STR, description='Search query (min 2 chars)', required=True)],
    summary="Search matches, articles, teams and IPTV channels"
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return Response({'matches': [], 'articles': [], 'teams': [], 'channels': []})

    matches = Match.objects.filter(
        Q(home_team__name__icontains=q) | Q(away_team__name__icontains=q) | Q(league__name__icontains=q)
    ).select_related('home_team', 'away_team', 'league__sport')[:8]

    articles = Article.objects.filter(
        status='published', published_at__lte=timezone.now()
    ).filter(
        Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q)
    ).select_related('author')[:8]

    teams = Team.objects.filter(
        Q(name__icontains=q) | Q(short_name__icontains=q)
    ).select_related('league__sport')[:5]

    channels = IPTVChannel.objects.filter(
        is_active=True, name__icontains=q
    )[:8]

    return Response({
        'matches': MatchSerializer(matches, many=True).data,
        'articles': ArticleSerializer(articles, many=True).data,
        'teams': TeamSerializer(teams, many=True).data,
        'channels': IPTVChannelSerializer(channels, many=True).data,
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
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not username or not email or not password:
        return Response({'error': 'username, email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password, role='registered')
    return Response({'message': 'Account created', 'username': user.username}, status=status.HTTP_201_CREATED)


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
        'avatar': serializers.URLField(required=False),
        'bio': serializers.CharField(required=False),
    }),
    responses={200: inline_serializer('UserProfileUpdateResponse', fields={'message': serializers.CharField()})},
    summary="Update the authenticated user's profile"
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user

    if request.method == 'GET':
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_premium': user.is_premium,
            'avatar': user.avatar,
            'bio': user.bio,
            'favorite_teams': user.favorite_teams,
            'notification_prefs': user.notification_prefs,
            'watch_history': user.watch_history[-20:],  # last 20
            'date_joined': user.date_joined,
        })

    allowed_fields = ['favorite_teams', 'notification_prefs', 'avatar', 'bio']
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    user.save(update_fields=allowed_fields)
    return Response({'message': 'Profile updated'})


@extend_schema(tags=['favorites'], summary='List user favorites')
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_favorites(request):
    favorites = UserFavorite.objects.filter(user=request.user)
    return Response(UserFavoriteSerializer(favorites, many=True).data)


@extend_schema(
    tags=['favorites'],
    request=inline_serializer('FavoriteRequest', fields={
        'item_type': serializers.ChoiceField(choices=['team', 'channel', 'league', 'player']),
        'item_id': serializers.IntegerField(),
        'item_name': serializers.CharField(required=False),
    }),
    responses={201: UserFavoriteSerializer},
    summary='Add an item to favorites'
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_favorite(request):
    item_type = request.data.get('item_type')
    item_id = request.data.get('item_id')
    item_name = request.data.get('item_name', '')

    if not item_type or not item_id:
        return Response({'error': 'item_type and item_id required'}, status=status.HTTP_400_BAD_REQUEST)

    fav, created = UserFavorite.objects.get_or_create(
        user=request.user, item_type=item_type, item_id=item_id,
        defaults={'item_name': item_name}
    )

    if not created:
        return Response({'error': 'Already in favorites'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(UserFavoriteSerializer(fav).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['favorites'], summary='Remove an item from favorites')
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_favorite(request, item_type, item_id):
    deleted, _ = UserFavorite.objects.filter(
        user=request.user, item_type=item_type, item_id=item_id
    ).delete()
    if deleted:
        return Response({'message': 'Removed from favorites'})
    return Response({'error': 'Favorite not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(tags=['iptv'], summary='Trigger IPTV playlist import (admin only)')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_iptv_import(request):
    if request.user.role not in ['streamer_admin', 'sysadmin']:
        return Response({'error': 'Insufficient permissions'}, status=status.HTTP_403_FORBIDDEN)

    from iptv_importer.tasks import sync_all_iptv_playlists
    result = sync_all_iptv_playlists.delay()

    AuditLog.objects.create(
        actor=request.user, action='trigger_iptv_import',
        object_type='IPTVChannel', object_id='all',
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    return Response({'message': 'IPTV import triggered', 'task_id': result.id})


def index(request):
    """Serve the React/Next.js frontend SPA"""
    return render(request, 'index.html')
