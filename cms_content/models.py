from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.api import APIField
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from django.http import JsonResponse
import json

# Custom blocks for content
class HeroBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=200, help_text="Main headline")
    subtitle = blocks.TextBlock(help_text="Supporting text", required=False)
    background_image = ImageChooserBlock(help_text="Hero background image")
    call_to_action_text = blocks.CharBlock(max_length=50, required=False)
    call_to_action_url = blocks.URLBlock(required=False)
    
    class Meta:
        template = 'blocks/hero_block.html'
        icon = 'image'
        label = 'Hero Section'

class MatchHighlightBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, help_text="Section title")
    featured_matches = blocks.ListBlock(
        blocks.StructBlock([
            ('home_team', blocks.CharBlock(max_length=50)),
            ('away_team', blocks.CharBlock(max_length=50)),
            ('match_time', blocks.DateTimeBlock()),
            ('is_live', blocks.BooleanBlock(default=False)),
            ('score_home', blocks.IntegerBlock(required=False)),
            ('score_away', blocks.IntegerBlock(required=False)),
            ('match_image', ImageChooserBlock(required=False)),
        ])
    )
    
    class Meta:
        template = 'blocks/match_highlight_block.html'
        icon = 'date'
        label = 'Match Highlights'

class NewsBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, help_text="News section title")
    featured_articles = blocks.ListBlock(
        blocks.StructBlock([
            ('headline', blocks.CharBlock(max_length=200)),
            ('excerpt', blocks.TextBlock(max_length=300)),
            ('image', ImageChooserBlock()),
            ('author', blocks.CharBlock(max_length=100)),
            ('publish_date', blocks.DateBlock()),
            ('article_url', blocks.URLBlock(required=False)),
        ])
    )
    
    class Meta:
        template = 'blocks/news_block.html'
        icon = 'doc-full'
        label = 'News Section'

class StatsBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, help_text="Statistics section title")
    stats = blocks.ListBlock(
        blocks.StructBlock([
            ('label', blocks.CharBlock(max_length=100)),
            ('value', blocks.CharBlock(max_length=50)),
            ('icon', blocks.CharBlock(max_length=50, help_text="CSS class or emoji")),
        ])
    )
    
    class Meta:
        template = 'blocks/stats_block.html'
        icon = 'table'
        label = 'Statistics'

class AdBlock(blocks.StructBlock):
    ad_title = blocks.CharBlock(max_length=100, help_text="Internal reference name")
    ad_image = ImageChooserBlock(help_text="Advertisement image")
    ad_url = blocks.URLBlock(help_text="Click destination URL")
    ad_text = blocks.TextBlock(help_text="Ad copy text", required=False)
    
    class Meta:
        template = 'blocks/ad_block.html'
        icon = 'image'
        label = 'Advertisement'

# Main Homepage model
class HomePage(RoutablePageMixin, Page):
    # Hero section
    hero_title = models.CharField(max_length=200, default="Welcome to Sports Portal")
    hero_subtitle = models.TextField(max_length=500, default="Your ultimate destination for live sports")
    hero_background = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Hero background image"
    )
    
    # Content sections
    content_sections = StreamField([
        ('hero', HeroBlock()),
        ('match_highlights', MatchHighlightBlock()),
        ('news_section', NewsBlock()),
        ('statistics', StatsBlock()),
        ('advertisement', AdBlock()),
    ], blank=True, use_json_field=True)
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_background'),
        ], heading="Hero Section"),
        FieldPanel('content_sections'),
    ]

    promote_panels = Page.promote_panels
    
    # API route for React frontend
    @route(r'^api/content/$')
    def api_content(self, request):
        content_data = {
            'hero': {
                'title': self.hero_title,
                'subtitle': self.hero_subtitle,
                'background_image': self.hero_background.file.url if self.hero_background else None,
            },
            'sections': []
        }
        
        for block in self.content_sections:
            section_data = {
                'type': block.block_type,
                'value': block.value
            }
            content_data['sections'].append(section_data)
        
        return JsonResponse(content_data)
    
    class Meta:
        verbose_name = "Homepage"

# Sports Content Pages
class SportPage(Page):
    sport_name = models.CharField(max_length=100, help_text="e.g., Cricket, Football, Tennis")
    sport_icon = models.CharField(max_length=10, help_text="Emoji or icon class", blank=True)
    description = RichTextField(help_text="Sport description and overview")
    
    # Featured content
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Featured sport image"
    )
    
    # Dynamic content sections
    sport_content = StreamField([
        ('match_highlights', MatchHighlightBlock()),
        ('news_section', NewsBlock()),
        ('statistics', StatsBlock()),
        ('advertisement', AdBlock()),
    ], blank=True, use_json_field=True)
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('sport_name'),
            FieldPanel('sport_icon'),
            FieldPanel('description'),
            FieldPanel('featured_image'),
        ], heading="Sport Information"),
        FieldPanel('sport_content'),
    ]
    
    class Meta:
        verbose_name = "Sport Page"

# News Article Page
class NewsArticlePage(Page):
    author = models.CharField(max_length=100, help_text="Article author name")
    publish_date = models.DateTimeField(auto_now_add=True)
    excerpt = models.TextField(max_length=300, help_text="Brief article summary")
    
    # Article content
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Article featured image"
    )
    
    article_content = RichTextField(help_text="Main article content")
    
    # Tags and categories
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    category = models.CharField(
        max_length=50,
        choices=[
            ('cricket', 'Cricket'),
            ('football', 'Football'),
            ('tennis', 'Tennis'),
            ('general', 'General Sports'),
        ],
        default='general'
    )
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('author'),
            FieldPanel('excerpt'),
            FieldPanel('featured_image'),
            FieldPanel('category'),
            FieldPanel('tags'),
        ], heading="Article Details"),
        FieldPanel('article_content'),
    ]
    
    # API fields for frontend
    api_fields = [
        APIField('author'),
        APIField('publish_date'),
        APIField('excerpt'),
        APIField('article_content'),
        APIField('category'),
        APIField('tags'),
    ]
    
    class Meta:
        verbose_name = "News Article"

# Snippets for reusable content
@register_snippet
class SiteSettings(ClusterableModel):
    site_name = models.CharField(max_length=100, default="Sports Portal")
    site_logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text="Site logo"
    )
    
    # Social media links
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # Contact information
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('site_name'),
            FieldPanel('site_logo'),
        ], heading="Site Branding"),
        MultiFieldPanel([
            FieldPanel('facebook_url'),
            FieldPanel('twitter_url'),
            FieldPanel('instagram_url'),
            FieldPanel('youtube_url'),
        ], heading="Social Media"),
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('contact_phone'),
        ], heading="Contact Information"),
    ]
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

@register_snippet
class Advertisement(models.Model):
    name = models.CharField(max_length=100, help_text="Internal ad name")
    ad_image = models.ForeignKey(
        'wagtailimages.Image',
        on_delete=models.CASCADE,
        related_name='+',
        help_text="Advertisement image"
    )
    ad_url = models.URLField(help_text="Click destination URL")
    ad_text = models.TextField(blank=True, help_text="Advertisement copy")
    
    # Placement settings
    placement = models.CharField(
        max_length=50,
        choices=[
            ('header', 'Header Banner'),
            ('sidebar', 'Sidebar'),
            ('footer', 'Footer'),
            ('inline', 'Inline Content'),
        ],
        default='sidebar'
    )
    
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    panels = [
        FieldPanel('name'),
        FieldPanel('ad_image'),
        FieldPanel('ad_url'),
        FieldPanel('ad_text'),
        FieldPanel('placement'),
        FieldPanel('is_active'),
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
        ], heading="Schedule"),
    ]
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Advertisement"
        ordering = ['-is_active', 'name']

# Live Match Widget (Snippet)
@register_snippet
class LiveMatchWidget(models.Model):
    widget_title = models.CharField(max_length=100, default="Live Matches")
    max_matches = models.IntegerField(default=5, help_text="Maximum matches to display")
    show_scores = models.BooleanField(default=True)
    show_time = models.BooleanField(default=True)
    
    # Styling options
    background_color = models.CharField(max_length=7, default="#0B6E4F", help_text="Hex color code")
    text_color = models.CharField(max_length=7, default="#FFFFFF", help_text="Hex color code")
    
    panels = [
        FieldPanel('widget_title'),
        FieldPanel('max_matches'),
        MultiFieldPanel([
            FieldPanel('show_scores'),
            FieldPanel('show_time'),
        ], heading="Display Options"),
        MultiFieldPanel([
            FieldPanel('background_color'),
            FieldPanel('text_color'),
        ], heading="Styling"),
    ]
    
    def __str__(self):
        return self.widget_title
    
    class Meta:
        verbose_name = "Live Match Widget"