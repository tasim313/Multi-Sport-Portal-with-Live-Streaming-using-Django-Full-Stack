import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class MatchConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for live match updates.
    Broadcasts: score_update, match_status_update, commentary_update
    """

    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.match_group_name = f'match_{self.match_id}'

        await self.channel_layer.group_add(self.match_group_name, self.channel_name)
        await self.accept()

        # Send current match data on connect
        match_data = await self.get_match_data()
        await self.send(text_data=json.dumps({'type': 'match_data', 'data': match_data}))

        # Send last 10 commentary lines
        commentary = await self.get_recent_commentary()
        if commentary:
            await self.send(text_data=json.dumps({'type': 'commentary_history', 'data': commentary}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.match_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            elif message_type == 'request_commentary':
                commentary = await self.get_recent_commentary()
                await self.send(text_data=json.dumps({'type': 'commentary_history', 'data': commentary}))

        except json.JSONDecodeError:
            pass

    async def score_update(self, event):
        await self.send(text_data=json.dumps({'type': 'score_update', 'data': event['data']}))

    async def match_status_update(self, event):
        await self.send(text_data=json.dumps({'type': 'status_update', 'data': event['data']}))

    async def commentary_update(self, event):
        await self.send(text_data=json.dumps({'type': 'commentary_update', 'data': event['data']}))

    @database_sync_to_async
    def get_match_data(self):
        from .models import Match
        from .views import MatchSerializer

        try:
            match = Match.objects.select_related(
                'home_team', 'away_team', 'league'
            ).get(id=self.match_id)
            return MatchSerializer(match).data
        except Match.DoesNotExist:
            return None

    @database_sync_to_async
    def get_recent_commentary(self):
        from .models import LiveCommentary

        qs = LiveCommentary.objects.filter(
            match_id=self.match_id
        ).order_by('-created_at')[:10]

        return [
            {
                'minute': c.minute,
                'period': c.period,
                'text': c.rewritten_text,
                'is_key': c.is_key_event,
                'event_type': c.score_event.event_type if c.score_event else None,
                'created_at': c.created_at.isoformat(),
            }
            for c in qs
        ]


class LiveScoreTickerConsumer(AsyncWebsocketConsumer):
    """
    Global live score ticker — broadcasts all live match scores.
    Used for the sticky header ticker on the frontend.
    """

    TICKER_GROUP = 'live_ticker'

    async def connect(self):
        await self.channel_layer.group_add(self.TICKER_GROUP, self.channel_name)
        await self.accept()

        # Send current live matches on connect
        matches = await self.get_live_matches()
        await self.send(text_data=json.dumps({'type': 'ticker_data', 'data': matches}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.TICKER_GROUP, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            pass

    async def ticker_update(self, event):
        await self.send(text_data=json.dumps({'type': 'ticker_update', 'data': event['data']}))

    @database_sync_to_async
    def get_live_matches(self):
        from .models import Match

        matches = Match.objects.filter(status='live').select_related(
            'home_team', 'away_team', 'league__sport'
        )[:20]

        return [
            {
                'id': m.id,
                'home': m.home_team.short_name,
                'away': m.away_team.short_name,
                'score': m.score_summary,
                'league': m.league.name,
                'sport': m.league.sport.name,
                'status': m.status,
            }
            for m in matches
        ]
