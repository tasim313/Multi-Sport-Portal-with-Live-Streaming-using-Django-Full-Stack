"""
Sport-specific scrapers that extract live match data from public APIs.
Uses free/open data sources — no scraping of paywalled or terms-violating content.
"""
import re
import logging
from typing import Optional, Dict, List, Any
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class FootballDataScraper(BaseCrawler):
    """
    Fetches football data from the free football-data.org API.
    Requires a free API key (set FOOTBALL_DATA_API_KEY env var).
    """
    BASE_URL = 'https://api.football-data.org/v4'

    def __init__(self, api_key: str = '', **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    def _get_headers(self) -> Dict[str, str]:
        headers = super()._get_headers()
        if self.api_key:
            headers['X-Auth-Token'] = self.api_key
        return headers

    def get_live_matches(self) -> List[Dict]:
        """Get currently live football matches."""
        data = self.fetch_json(f'{self.BASE_URL}/matches', params={'status': 'LIVE'})
        if not data:
            return []
        return data.get('matches', [])

    def get_match(self, match_id: int) -> Optional[Dict]:
        """Get details for a specific match."""
        return self.fetch_json(f'{self.BASE_URL}/matches/{match_id}')

    def get_competitions(self) -> List[Dict]:
        """Get available competitions."""
        data = self.fetch_json(f'{self.BASE_URL}/competitions')
        return data.get('competitions', []) if data else []

    def parse_score_events(self, match_data: Dict) -> List[Dict]:
        """Parse score events from football-data.org match response."""
        events = []
        goals = match_data.get('goals', [])
        for goal in goals:
            events.append({
                'event_type': 'goal',
                'minute': goal.get('minute'),
                'player_name': goal.get('scorer', {}).get('name', ''),
                'team_side': 'home' if goal.get('team', {}).get('id') == match_data.get('homeTeam', {}).get('id') else 'away',
                'payload': {
                    'scorer': goal.get('scorer', {}),
                    'assist': goal.get('assist', {}),
                    'type': goal.get('type', 'REGULAR'),
                }
            })
        return events


class CricketAPIScraper(BaseCrawler):
    """
    Fetches cricket data from cricapi.com (free tier available).
    Set CRICKET_API_KEY env var.
    """
    BASE_URL = 'https://api.cricapi.com/v1'

    def __init__(self, api_key: str = '', **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key

    def get_current_matches(self) -> List[Dict]:
        """Get currently live cricket matches."""
        data = self.fetch_json(
            f'{self.BASE_URL}/currentMatches',
            params={'apikey': self.api_key, 'offset': 0}
        )
        if not data or data.get('status') != 'success':
            return []
        return data.get('data', [])

    def get_match_scorecard(self, match_id: str) -> Optional[Dict]:
        """Get scorecard for a specific match."""
        return self.fetch_json(
            f'{self.BASE_URL}/match_scorecard',
            params={'apikey': self.api_key, 'id': match_id}
        )

    def parse_score_events(self, scorecard_data: Dict) -> List[Dict]:
        """Parse wickets and boundaries from scorecard."""
        events = []
        score_list = scorecard_data.get('score', [])
        for innings in score_list:
            over_str = innings.get('overs', '')
            try:
                over = float(over_str)
            except (ValueError, TypeError):
                over = 0

            events.append({
                'event_type': 'boundary',
                'minute': None,
                'player_name': '',
                'team_side': 'home',
                'payload': {
                    'innings': innings.get('inning', ''),
                    'runs': innings.get('r', 0),
                    'wickets': innings.get('w', 0),
                    'overs': over,
                }
            })
        return events


class TheSportsDBScraper(BaseCrawler):
    """
    Fetches sports data from TheSportsDB.com free API.
    Works for Football, Basketball, Baseball, Tennis, etc.
    """
    BASE_URL = 'https://www.thesportsdb.com/api/v1/json/3'

    def get_live_events(self) -> List[Dict]:
        """Get all live events (free tier: soccer only)."""
        data = self.fetch_json(f'{self.BASE_URL}/livescore.php')
        if not data:
            return []
        return data.get('events', []) or []

    def get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Get event details by ID."""
        data = self.fetch_json(
            f'{self.BASE_URL}/lookupevent.php',
            params={'id': event_id}
        )
        if not data:
            return None
        events = data.get('events', [])
        return events[0] if events else None

    def get_team(self, team_id: str) -> Optional[Dict]:
        """Get team details."""
        data = self.fetch_json(
            f'{self.BASE_URL}/lookupteam.php',
            params={'id': team_id}
        )
        if not data:
            return None
        teams = data.get('teams', [])
        return teams[0] if teams else None

    def parse_score_event(self, event_data: Dict) -> Dict:
        """Convert TheSportsDB event to our internal format."""
        home_score = event_data.get('intHomeScore') or 0
        away_score = event_data.get('intAwayScore') or 0
        return {
            'home_score': int(home_score),
            'away_score': int(away_score),
            'status': event_data.get('strStatus', ''),
            'progress': event_data.get('strProgress', ''),
            'time': event_data.get('strTime', ''),
        }


class UFCMMADScraper(BaseCrawler):
    """Fetches UFC/MMA event data from public sources."""
    BASE_URL = 'https://www.thesportsdb.com/api/v1/json/3'

    def get_upcoming_events(self, league_id: str = '4443') -> List[Dict]:
        """Get upcoming UFC events."""
        data = self.fetch_json(
            f'{self.BASE_URL}/eventsseason.php',
            params={'id': league_id, 's': '2024-2025'}
        )
        if not data:
            return []
        return data.get('events', []) or []
