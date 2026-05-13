import hashlib
import os
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from sports.models import IPTVChannel


ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
DEFAULT_PLAYLIST_URL = 'https://iptv-org.github.io/iptv/index.m3u'


def parse_extinf(line):
    attrs = dict(ATTR_RE.findall(line))
    _, _, name = line.partition(',')
    return attrs, name.strip()


def channel_source_id(attrs, stream_url):
    tvg_id = attrs.get('tvg-id', '').strip()
    if tvg_id:
        return f'iptv-org:{tvg_id}'
    digest = hashlib.sha256(stream_url.encode('utf-8')).hexdigest()[:24]
    return f'iptv-org:url:{digest}'


class Command(BaseCommand):
    help = 'Import public IPTV channels from an iptv-org M3U playlist.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            default=os.environ.get('IPTV_ORG_PLAYLIST_URL', DEFAULT_PLAYLIST_URL),
            help='M3U playlist URL to import.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Maximum number of channels to import. 0 means no limit.',
        )
        parser.add_argument(
            '--sports-only',
            action='store_true',
            help='Only import channels whose group/category contains "sport".',
        )
        parser.add_argument(
            '--deactivate-missing',
            action='store_true',
            help='Deactivate existing iptv-org channels that are not in this import.',
        )

    def handle(self, *args, **options):
        playlist_url = options['url']
        request = Request(
            playlist_url,
            headers={'User-Agent': 'SportsPortal IPTV importer (+https://github.com/iptv-org/iptv)'},
        )

        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode('utf-8', errors='replace')
        except URLError as exc:
            raise CommandError(f'Could not download playlist: {exc}') from exc

        lines = [line.strip() for line in body.splitlines() if line.strip()]
        created = 0
        updated = 0
        skipped = 0
        seen_ids = set()
        pending_attrs = None
        pending_name = ''

        for line in lines:
            if line.startswith('#EXTINF:'):
                pending_attrs, pending_name = parse_extinf(line)
                continue

            if line.startswith('#') or not pending_attrs:
                continue

            stream_url = line
            attrs = pending_attrs
            name = pending_name or attrs.get('tvg-name') or attrs.get('tvg-id') or 'Untitled Channel'
            category = attrs.get('group-title', '').strip()

            pending_attrs = None
            pending_name = ''

            if options['sports_only'] and 'sport' not in category.lower():
                skipped += 1
                continue

            source_id = channel_source_id(attrs, stream_url)
            seen_ids.add(source_id)
            base_slug = slugify(name)[:240] or 'channel'
            slug = base_slug
            if IPTVChannel.objects.filter(slug=slug).exclude(source_id=source_id).exists():
                slug = f'{base_slug}-{source_id.split(":")[-1][:12]}'

            defaults = {
                'name': name[:255],
                'slug': slug[:280],
                'stream_url': stream_url,
                'source_name': 'iptv-org',
                'source_url': playlist_url,
                'tvg_id': attrs.get('tvg-id', '')[:255],
                'logo': attrs.get('tvg-logo', '')[:1000],
                'category': category[:120],
                'country': attrs.get('tvg-country', '')[:120],
                'country_code': attrs.get('tvg-country', '')[:12],
                'language': attrs.get('tvg-language', '')[:120],
                'is_active': True,
                'is_featured': 'sport' in category.lower(),
            }
            _, was_created = IPTVChannel.objects.update_or_create(
                source_id=source_id,
                defaults=defaults,
            )
            created += int(was_created)
            updated += int(not was_created)

            if options['limit'] and created + updated >= options['limit']:
                break

        if options['deactivate_missing'] and seen_ids:
            IPTVChannel.objects.filter(source_name='iptv-org').exclude(source_id__in=seen_ids).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Imported IPTV channels: {created} created, {updated} updated, {skipped} skipped.'
        ))
