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
        settings.social_links = [
            SocialLink(platform="instagram", url="https://instagram.com/example"),
            SocialLink(label="LinkedIn", url="https://linkedin.com/in/example"),
        ]
        settings.save()

        html = self.client.get("/").content.decode()
        footer = html[html.index("<footer") :]
        self.assertIn("Max Mustermann", footer)
        self.assertIn('href="mailto:max@example.com"', footer)
        self.assertIn('href="tel:+49151000000"', footer)
        self.assertIn('href="/impressum/"', footer)
        # Bekannte Plattform: Icon mit Namen für Screenreader, kein sichtbarer Text.
        self.assertIn('aria-label="Instagram"', footer)
        self.assertIn("<svg", footer)
        # Ohne Plattform: Textlink.
        self.assertIn(">LinkedIn</a>", footer)

    def test_empty_settings_render_without_errors(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("mailto:", response.content.decode())


class SocialLinkTests(TestCase):
    def test_link_without_platform_needs_label(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            SocialLink(url="https://example.com").clean()
        SocialLink(url="https://example.com", label="Blog").clean()
        SocialLink(url="https://example.com", platform="tiktok").clean()

    def test_name_and_icon(self):
        link = SocialLink(platform="tiktok", url="https://tiktok.com/@example")
        self.assertEqual(link.name, "TikTok")
        self.assertTrue(link.icon_path)
        self.assertEqual(SocialLink(label="Blog", url="https://example.com").icon_path, "")


class SeedSiteTests(TestCase):
    def run_command(self, payload=b"zip"):
        import tempfile
        from io import StringIO
        from unittest import mock

        from django.core.management import call_command
        from django.test import override_settings

        def fake_download(url):
            if payload is None:
                raise OSError("kein Netz")
            return payload

        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            with mock.patch("core.management.commands.seed_site.download", fake_download):
                call_command("seed_site", stdout=StringIO())

    def test_creates_pages_and_fills_settings(self):
        self.run_command()
        site = Site.objects.get(is_default_site=True)
        menu = site.root_page.get_children().live().in_menu()
        self.assertEqual(
            [page.title for page in menu], ["Commercial", "Outdoor", "Other", "Booking", "About"]
        )
        settings = SiteSettings.for_site(site)
        self.assertEqual(settings.postal_code_city, "59494 Soest")
        self.assertEqual(settings.legal_page.slug, "impressum")
        self.assertIsNotNone(settings.footer_download)
        self.assertEqual(
            [link.platform for link in settings.social_links.all()], ["instagram", "tiktok"]
        )

    def test_second_run_keeps_manual_changes_and_adds_nothing(self):
        self.run_command()
        site = Site.objects.get(is_default_site=True)
        settings = SiteSettings.for_site(site)
        settings.phone = "+49 151 111111"
        settings.save()
        pages_before = Page.objects.count()

        self.run_command()

        settings = SiteSettings.for_site(site)
        self.assertEqual(settings.phone, "+49 151 111111")
        self.assertEqual(Page.objects.count(), pages_before)
        self.assertEqual(settings.social_links.count(), 2)

    def test_failed_download_does_not_stop_the_rest(self):
        self.run_command(payload=None)
        settings = SiteSettings.for_site(Site.objects.get(is_default_site=True))
        self.assertIsNone(settings.footer_download)
        self.assertEqual(settings.contact_name, "Jonas Dülberg")
