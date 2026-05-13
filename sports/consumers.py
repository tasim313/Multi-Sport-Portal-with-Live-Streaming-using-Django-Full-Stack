import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


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

        # Send current match data on connect
        match_data = await self.get_match_data()
        await self.send(text_data=json.dumps({
            'type': 'match_data',
            'data': match_data
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.match_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

        except json.JSONDecodeError:
            pass

    async def score_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'score_update',
            'data': event['data']
        }))

    async def match_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))

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
