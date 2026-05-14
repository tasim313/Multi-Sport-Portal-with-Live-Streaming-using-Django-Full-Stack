"""
AI Commentary Rewriter.
Rewrites raw crawled commentary using Claude API (Anthropic) or OpenAI.
Never shows original crawled text to users — always rewrites it.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

REWRITE_PROMPT_TEMPLATE = """You are a professional sports commentator. Rewrite the following sports commentary in a fresh, engaging, human-like style. Keep it concise (1-2 sentences max). Do not copy the original wording. Make it sound natural and exciting.

Sport: {sport}
Original: {original_text}

Rewritten commentary (no quotes, no explanation):"""

SUMMARIZE_PROMPT_TEMPLATE = """You are a professional sports journalist. Write a brief match summary (2-3 sentences) based on the following match data.

Match: {home_team} vs {away_team}
Score: {home_score} - {away_score}
League: {league}
Status: {status}
Key events: {events}

Match summary (no quotes, no explanation):"""


def _rewrite_with_anthropic(original_text: str, sport: str = 'football') -> Optional[str]:
    """Rewrite commentary using Claude API."""
    try:
        import anthropic
        from decouple import config

        api_key = config('ANTHROPIC_API_KEY', default='')
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            sport=sport,
            original_text=original_text
        )

        message = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=150,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return message.content[0].text.strip()

    except ImportError:
        logger.warning("anthropic package not installed")
        return None
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        return None


def _rewrite_with_openai(original_text: str, sport: str = 'football') -> Optional[str]:
    """Rewrite commentary using OpenAI API."""
    try:
        import openai
        from decouple import config

        api_key = config('OPENAI_API_KEY', default='')
        if not api_key:
            return None

        client = openai.OpenAI(api_key=api_key)
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            sport=sport,
            original_text=original_text
        )

        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=150,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()

    except ImportError:
        logger.warning("openai package not installed")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def _fallback_rewrite(original_text: str, sport: str = 'football') -> str:
    """
    Simple rule-based rewriter as fallback when no AI API is available.
    Handles basic paraphrasing by rearranging sentence elements.
    """
    import random

    # Simple sport-specific templates
    templates_by_keyword = {
        'goal': [
            "The net ripples as the ball finds its mark.",
            "A clinical finish makes it onto the scoresheet.",
            "The crowd erupts as another goal goes in.",
        ],
        'scores': [
            "Another one goes in for the attacking side.",
            "A well-taken effort increases the tally.",
        ],
        'wicket': [
            "A big breakthrough as a wicket falls.",
            "The batting side loses another player.",
            "The bowler strikes to remove the batsman.",
        ],
        'boundary': [
            "The ball races to the rope for four.",
            "A crisp shot dispatches the ball to the boundary.",
        ],
        'six': [
            "Incredible shot! The ball sails over the boundary rope.",
            "The batsman sends that one out of the ground.",
        ],
        'card': [
            "The referee reaches for the card.",
            "Discipline proves costly here.",
        ],
        'substitution': [
            "A tactical change from the bench.",
            "Fresh legs are introduced into the game.",
        ],
        'penalty': [
            "A spot kick is awarded.",
            "The referee points to the penalty spot.",
        ],
    }

    text_lower = original_text.lower()
    for keyword, alternatives in templates_by_keyword.items():
        if keyword in text_lower:
            return random.choice(alternatives)

    # Generic fallback: rephrase as present-tense action
    return f"Action continues as the game stays tight."


def rewrite_commentary(
    original_text: str,
    sport: str = 'football',
    language: str = 'en'
) -> str:
    """
    Main entry point: rewrite raw commentary text.
    Tries Anthropic Claude first, then OpenAI, then rule-based fallback.
    Always returns a rewritten string (never the original).
    """
    if not original_text or not original_text.strip():
        return ''

    # Try AI providers in order
    result = _rewrite_with_anthropic(original_text, sport)
    if result:
        logger.debug("Commentary rewritten via Anthropic")
        return result

    result = _rewrite_with_openai(original_text, sport)
    if result:
        logger.debug("Commentary rewritten via OpenAI")
        return result

    # Fallback
    result = _fallback_rewrite(original_text, sport)
    logger.debug("Commentary rewritten via rule-based fallback")
    return result


def generate_match_summary(
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    league: str,
    status: str,
    events: list,
    sport: str = 'football',
) -> str:
    """Generate an AI match summary."""
    events_str = ', '.join([
        f"{e.get('event_type', '')} by {e.get('player_name', 'unknown')} ({e.get('minute', '?')}\')"
        for e in events[:5]
    ])

    prompt = SUMMARIZE_PROMPT_TEMPLATE.format(
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        league=league,
        status=status,
        events=events_str or 'No key events yet',
    )

    # Try Anthropic
    try:
        import anthropic
        from decouple import config

        api_key = config('ANTHROPIC_API_KEY', default='')
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=200,
                messages=[{'role': 'user', 'content': prompt}]
            )
            return message.content[0].text.strip()
    except Exception as e:
        logger.error(f"Summary generation error: {e}")

    # Fallback
    if home_score > away_score:
        return f"{home_team} lead {home_score}-{away_score} against {away_team} in this {league} encounter."
    elif away_score > home_score:
        return f"{away_team} are ahead {away_score}-{home_score} in their match against {home_team}."
    else:
        return f"{home_team} and {away_team} are level at {home_score}-{away_score} in the {league}."
