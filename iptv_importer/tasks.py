"""
Celery tasks for IPTV channel import and maintenance.
"""
import logging
import hashlib
from celery import shared_task
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger(__name__)


def _make_source_id(name: str, stream_url: str) -> str:
    """Create a stable unique ID for a channel from name + URL."""
    raw = f"{name}::{stream_url}"
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def _make_slug(name: str, source_id: str) -> str:
    """Create a unique slug from channel name + source_id suffix."""
    base_slug = slugify(name or 'channel')[:220]
    if not base_slug:
        base_slug = 'channel'
    return f"{base_slug}-{source_id[:12]}"


@shared_task(bind=True, max_retries=3)
def import_iptv_playlist(self, playlist_url: str, category_override: str = ''):
    """
    Fetch and import a single M3U playlist.
    Creates or updates IPTVChannel records.
    Returns a summary dict.
    """
    from sports.models import IPTVChannel
    from .m3u_parser import fetch_m3u_playlist, parse_m3u_content, normalize_country_code, map_group_to_category

    try:
        logger.info(f"Importing IPTV playlist: {playlist_url}")
        content = fetch_m3u_playlist(playlist_url)

        if not content:
            logger.warning(f"Empty content from {playlist_url}")
            return {'created': 0, 'updated': 0, 'errors': 0}

        created = updated = errors = 0

        for channel_data in parse_m3u_content(content):
            try:
                name = channel_data.get('name', '').strip()
                stream_url = channel_data.get('stream_url', '').strip()

                if not name or not stream_url:
                    continue

                source_id = _make_source_id(name, stream_url)
                slug = _make_slug(name, source_id)

                category = category_override or map_group_to_category(
                    channel_data.get('group_title', '')
                )
                country_code = normalize_country_code(channel_data.get('country', ''))

                defaults = {
                    'name': name[:255],
                    'stream_url': stream_url[:2000],
                    'source_url': playlist_url[:1000],
                    'source_name': 'iptv-org',
                    'tvg_id': channel_data.get('tvg_id', '')[:255],
                    'logo': channel_data.get('logo', '')[:1000],
                    'category': category[:120],
                    'country': channel_data.get('country', '')[:120],
                    'country_code': country_code[:12],
                    'language': channel_data.get('language', '')[:120],
                    'is_active': True,
                    'is_working': True,
                }

                obj, was_created = IPTVChannel.objects.update_or_create(
                    source_id=source_id,
                    defaults={**defaults, 'slug': slug}
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

            except Exception as e:
                logger.error(f"Error processing channel '{channel_data.get('name')}': {e}")
                errors += 1

        logger.info(f"Playlist import done: {created} created, {updated} updated, {errors} errors")
        return {'created': created, 'updated': updated, 'errors': errors}

    except Exception as exc:
        logger.error(f"Playlist import failed for {playlist_url}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def sync_all_iptv_playlists():
    """
    Sync all configured iptv-org category playlists.
    Called by Celery Beat schedule.
    """
    from .m3u_parser import IPTV_ORG_PLAYLISTS

    results = []
    for category, url in IPTV_ORG_PLAYLISTS.items():
        result = import_iptv_playlist.delay(url, category_override=category.title())
        results.append({'category': category, 'task_id': result.id})
        logger.info(f"Queued import for {category}: {result.id}")

    return results


@shared_task
def check_dead_streams(batch_size: int = 100):
    """
    Check a batch of IPTV channels for dead streams.
    Marks is_working=False for unreachable streams.
    """
    from sports.models import IPTVChannel
    from .m3u_parser import check_stream_health

    # Process oldest-checked channels first
    channels = IPTVChannel.objects.filter(is_active=True).order_by(
        'last_checked'
    )[:batch_size]

    dead = 0
    alive = 0
    for channel in channels:
        is_ok = check_stream_health(channel.stream_url)
        channel.is_working = is_ok
        channel.last_checked = timezone.now()
        channel.save(update_fields=['is_working', 'last_checked'])
        if is_ok:
            alive += 1
        else:
            dead += 1
            logger.debug(f"Dead stream: {channel.name} - {channel.stream_url}")

    logger.info(f"Stream health check: {alive} alive, {dead} dead in batch of {batch_size}")
    return {'alive': alive, 'dead': dead}


@shared_task
def deactivate_dead_channels(threshold_days: int = 7):
    """
    Deactivate channels that have been dead for more than threshold_days.
    """
    from sports.models import IPTVChannel
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=threshold_days)
    deactivated = IPTVChannel.objects.filter(
        is_working=False,
        last_checked__lt=cutoff
    ).update(is_active=False)

    logger.info(f"Deactivated {deactivated} dead channels")
    return {'deactivated': deactivated}
