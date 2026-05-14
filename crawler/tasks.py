"""
Celery tasks for the sports data crawler.
Polls external APIs, stores match events and commentary.
"""
import logging
from celery import shared_task
from django.utils import timezone
from decouple import config

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def crawl_live_football(self):
    """
    Fetch live football match data from football-data.org
    and update our match records + broadcast via WebSocket.
    """
    from sports.models import Match, ScoreEvent, LiveCommentary
    from .scrapers import FootballDataScraper

    api_key = config('FOOTBALL_DATA_API_KEY', default='')
    scraper = FootballDataScraper(api_key=api_key)

    try:
        live_matches = scraper.get_live_matches()
        logger.info(f"Fetched {len(live_matches)} live football matches")

        for match_data in live_matches:
            _process_football_match(match_data, scraper)

        return {'processed': len(live_matches)}
    except Exception as exc:
        logger.error(f"crawl_live_football failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


def _process_football_match(match_data: dict, scraper):
    """Process a single football match from external API data."""
    from sports.models import Match, ScoreEvent, LiveCommentary
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    ext_id = str(match_data.get('id', ''))
    if not ext_id:
        return

    # Try to find matching match by external ID in metadata
    try:
        match = Match.objects.get(metadata__external_id=ext_id)
    except Match.DoesNotExist:
        return
    except Match.MultipleObjectsReturned:
        match = Match.objects.filter(metadata__external_id=ext_id).first()

    # Update score
    score = match_data.get('score', {})
    full_time = score.get('fullTime', {})
    home_score = full_time.get('home') or 0
    away_score = full_time.get('away') or 0

    match.score_summary = {
        'home': home_score,
        'away': away_score,
        'details': score
    }
    match.save(update_fields=['score_summary', 'updated_at'])

    # Parse and store events
    events = scraper.parse_score_events(match_data)
    for event in events:
        ScoreEvent.objects.get_or_create(
            match=match,
            event_type=event['event_type'],
            minute=event.get('minute'),
            player_name=event.get('player_name', ''),
            defaults={
                'period': '1H' if (event.get('minute') or 0) <= 45 else '2H',
                'payload': event.get('payload', {}),
                'team_side': event.get('team_side', ''),
            }
        )

    # Broadcast update via WebSocket
    channel_layer = get_channel_layer()
    try:
        async_to_sync(channel_layer.group_send)(
            f'match_{match.id}',
            {
                'type': 'score_update',
                'data': {
                    'match_id': match.id,
                    'score': match.score_summary,
                    'status': match.status,
                }
            }
        )
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed for match {match.id}: {e}")


@shared_task(bind=True, max_retries=3)
def crawl_live_cricket(self):
    """Fetch live cricket match data from cricapi."""
    from sports.models import Match, ScoreEvent
    from .scrapers import CricketAPIScraper

    api_key = config('CRICKET_API_KEY', default='')
    if not api_key:
        logger.info("No CRICKET_API_KEY set, skipping cricket crawl")
        return {'skipped': True}

    scraper = CricketAPIScraper(api_key=api_key)

    try:
        matches = scraper.get_current_matches()
        logger.info(f"Fetched {len(matches)} live cricket matches")
        return {'processed': len(matches)}
    except Exception as exc:
        logger.error(f"crawl_live_cricket failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True, max_retries=3)
def crawl_thesportsdb(self):
    """Fetch live event data from TheSportsDB."""
    from sports.models import Match
    from .scrapers import TheSportsDBScraper
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    scraper = TheSportsDBScraper()

    try:
        events = scraper.get_live_events()
        logger.info(f"Fetched {len(events)} live events from TheSportsDB")

        channel_layer = get_channel_layer()
        processed = 0

        for event in events:
            ext_id = str(event.get('idEvent', ''))
            if not ext_id:
                continue

            try:
                match = Match.objects.get(metadata__sportsdb_id=ext_id)
            except Match.DoesNotExist:
                continue

            score_data = scraper.parse_score_event(event)
            match.score_summary = score_data
            match.save(update_fields=['score_summary', 'updated_at'])

            try:
                async_to_sync(channel_layer.group_send)(
                    f'match_{match.id}',
                    {
                        'type': 'score_update',
                        'data': {
                            'match_id': match.id,
                            'score': score_data,
                            'status': match.status,
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"WebSocket broadcast failed: {e}")

            processed += 1

        return {'processed': processed}
    except Exception as exc:
        logger.error(f"crawl_thesportsdb failed: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task
def generate_commentary_for_events():
    """
    Find ScoreEvents without LiveCommentary and queue AI rewriting.
    Runs periodically to keep commentary up to date.
    """
    from sports.models import ScoreEvent, LiveCommentary
    from ai_commentary.tasks import rewrite_commentary_for_event

    events_without_commentary = ScoreEvent.objects.filter(
        commentary__isnull=True,
        match__status='live'
    ).values_list('id', flat=True)[:20]

    queued = 0
    for event_id in events_without_commentary:
        rewrite_commentary_for_event.delay(event_id)
        queued += 1

    logger.info(f"Queued AI commentary rewrite for {queued} events")
    return {'queued': queued}
