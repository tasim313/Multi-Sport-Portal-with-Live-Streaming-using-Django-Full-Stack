from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


@shared_task
def auto_start_matches():
    """Set scheduled matches to 'live' when their start time has passed."""
    from .models import Match
    from .views import MatchSerializer

    now = timezone.now()
    started = Match.objects.filter(
        status='scheduled',
        start_time__lte=now
    )
    count = started.count()
    if count:
        started.update(status='live')
        logger.info(f"auto_start_matches: set {count} match(es) to live")

        # Broadcast status update for each
        channel_layer = get_channel_layer()
        for match in Match.objects.filter(status='live', start_time__lte=now):
            try:
                async_to_sync(channel_layer.group_send)(
                    f'match_{match.id}',
                    {
                        'type': 'match_status_update',
                        'data': {'status': 'live', 'match_id': match.id}
                    }
                )
            except Exception as e:
                logger.warning(f"Could not broadcast match {match.id}: {e}")

    return f"{count} matches started"


@shared_task
def auto_finish_matches():
    """Set live matches to 'finished' if they have an end_time in the past."""
    from .models import Match

    now = timezone.now()
    finished = Match.objects.filter(
        status='live',
        end_time__isnull=False,
        end_time__lte=now
    )
    count = finished.count()
    if count:
        finished.update(status='finished')
        logger.info(f"auto_finish_matches: finished {count} match(es)")

    return f"{count} matches finished"


@shared_task
def cleanup_old_audit_logs():
    """Delete audit logs older than 90 days."""
    from .models import AuditLog
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
    logger.info(f"cleanup_old_audit_logs: deleted {deleted} entries")
    return f"{deleted} audit log entries deleted"
