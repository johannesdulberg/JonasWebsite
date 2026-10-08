from django.test import TestCase
from wagtail.models import Page, Site

from core.models import SiteSettings, SocialLink
from home.models import HomePage


class HeaderFooterTests(TestCase):
    def setUp(self):
        self.site = Site.objects.get(is_default_site=True)
        self.home = self.site.root_page
        self.gallery = self.home.add_child(
            instance=HomePage(title="Commercial", slug="commercial", show_in_menus=True)
        )
        self.home.add_child(instance=HomePage(title="Versteckt", slug="versteckt"))
        self.home.add_child(
            instance=HomePage(title="Entwurf", slug="entwurf", show_in_menus=True, live=False)
        )
        self.legal = self.home.add_child(instance=HomePage(title="Impressum", slug="impressum"))

    def test_nav_lists_home_and_menu_pages_only(self):
        html = self.client.get("/").content.decode()
        nav = html[html.index('id="main-nav"') : html.index("</nav>")]
        self.assertIn(">Commercial</a>", nav)
        self.assertIn(f">{self.home.title}</a>", nav)
        self.assertNotIn("Versteckt", nav)
        self.assertNotIn("Entwurf", nav)

    def test_nav_marks_current_page(self):
        html = self.client.get("/commercial/").content.decode()
        nav = html[html.index('id="main-nav"') : html.index("</nav>")]
        self.assertEqual(nav.count('aria-current="page"'), 1)
        self.assertRegex(nav, r'aria-current="page">Commercial</a>')

    def test_footer_shows_settings(self):
        settings = SiteSettings.for_site(self.site)
        settings.contact_name = "Max Mustermann"
        settings.email = "max@example.com"
        settings.phone = "+49 151 000000"
        settings.legal_page = Page.objects.get(pk=self.legal.pk)
        settings.social_links = [SocialLink(label="Instagram", url="https://instagram.com/example")]
        settings.save()

        html = self.client.get("/").content.decode()
        footer = html[html.index("<footer") :]
        self.assertIn("Max Mustermann", footer)
        self.assertIn('href="mailto:max@example.com"', footer)
        self.assertIn('href="tel:+49151000000"', footer)
        self.assertIn('href="/impressum/"', footer)
        self.assertIn(">Instagram</a>", footer)

    def test_empty_settings_render_without_errors(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("mailto:", response.content.decode())
