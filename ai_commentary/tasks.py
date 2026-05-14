"""
Celery tasks for AI commentary generation.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def rewrite_commentary_for_event(self, score_event_id: int):
    """
    Rewrite commentary for a specific ScoreEvent.
    Creates a LiveCommentary record with AI-rewritten text.
    """
    from sports.models import ScoreEvent, LiveCommentary
    from .rewriter import rewrite_commentary

    try:
        event = ScoreEvent.objects.select_related(
            'match__league__sport',
            'match__home_team',
            'match__away_team',
        ).get(id=score_event_id)
    except ScoreEvent.DoesNotExist:
        logger.warning(f"ScoreEvent {score_event_id} not found")
        return

    # Skip if commentary already exists
    if hasattr(event, 'commentary') and event.commentary:
        return

    sport = event.match.league.sport.name.lower()
    player = event.player_name or event.payload.get('player', '')
    minute = event.minute

    # Build original text from event data
    original_text = _build_original_text(event, player, minute)

    try:
        rewritten = rewrite_commentary(original_text, sport=sport)

        LiveCommentary.objects.create(
            match=event.match,
            minute=minute,
            period=event.period,
            original_text=original_text,
            rewritten_text=rewritten,
            source='crawled',
            language='en',
            is_key_event=event.event_type in ['goal', 'wicket', 'red_card', 'penalty'],
            score_event=event,
        )

        logger.debug(f"Commentary created for event {score_event_id}: {rewritten[:60]}")

        # Broadcast to WebSocket
        _broadcast_commentary(event.match.id, minute, rewritten, event.event_type)

    except Exception as exc:
        logger.error(f"Commentary rewrite failed for event {score_event_id}: {exc}")
        raise self.retry(exc=exc, countdown=10)


def _build_original_text(event, player: str, minute) -> str:
    """Build a raw commentary sentence from event data."""
    event_templates = {
        'goal': f"{player} scores{'at minute ' + str(minute) if minute else ''}.",
        'wicket': f"{player} is out{'at over ' + str(minute) if minute else ''}.",
        'boundary': f"{player} hits a boundary.",
        'six': f"{player} hits a six.",
        'yellow_card': f"{player} receives a yellow card{'in minute ' + str(minute) if minute else ''}.",
        'red_card': f"{player} is sent off with a red card.",
        'substitution': f"Substitution: {player} comes on.",
        'penalty': f"Penalty awarded{'in minute ' + str(minute) if minute else ''}.",
        'var_check': "VAR is checking the decision.",
        'period_start': f"The {event.period} period begins.",
        'period_end': f"The {event.period} period ends.",
    }
    return event_templates.get(event.event_type, f"{event.event_type} event occurred.")


def _broadcast_commentary(match_id: int, minute, text: str, event_type: str):
    """Broadcast new commentary to WebSocket group."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'match_{match_id}',
            {
                'type': 'commentary_update',
                'data': {
                    'minute': minute,
                    'text': text,
                    'event_type': event_type,
                    'is_key': event_type in ['goal', 'wicket', 'red_card', 'penalty'],
                }
            }
        )
    except Exception as e:
        logger.warning(f"Commentary WebSocket broadcast failed: {e}")


@shared_task
def bulk_rewrite_pending_commentary(match_id: int, limit: int = 50):
    """
    Rewrite commentary for all pending events in a match.
    Used when a match becomes live.
    """
    from sports.models import ScoreEvent

    event_ids = ScoreEvent.objects.filter(
        match_id=match_id,
        commentary__isnull=True
    ).values_list('id', flat=True)[:limit]

    for event_id in event_ids:
        rewrite_commentary_for_event.delay(event_id)

    return {'queued': len(event_ids)}


@shared_task
def generate_post_match_summary(match_id: int):
    """
    Generate an AI post-match summary when a match finishes.
    Stores the summary in match metadata.
    """
    from sports.models import Match, ScoreEvent
    from .rewriter import generate_match_summary

    try:
        match = Match.objects.select_related(
            'home_team', 'away_team', 'league__sport'
        ).get(id=match_id)
    except Match.DoesNotExist:
        return

    events = list(
        ScoreEvent.objects.filter(match=match)
        .values('event_type', 'player_name', 'minute')[:10]
    )

    summary = generate_match_summary(
        home_team=match.home_team.name,
        away_team=match.away_team.name,
        home_score=match.score_summary.get('home', 0),
        away_score=match.score_summary.get('away', 0),
        league=match.league.name,
        status=match.status,
        events=events,
        sport=match.league.sport.name.lower(),
    )

    match.metadata['ai_summary'] = summary
    match.save(update_fields=['metadata'])

    logger.info(f"Post-match summary generated for match {match_id}")
    return {'summary': summary}
