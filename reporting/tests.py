from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .forms import ReportForm


class ReportFormTests(SimpleTestCase):
    def test_required_fields_reject_whitespace(self):
        form = ReportForm({"title": "   ", "description": "\n "})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"title", "description"})

    def test_limits_and_optional_location(self):
        valid = {"title": "a" * 120, "description": "b" * 2000}
        self.assertTrue(ReportForm(valid).is_valid())
        for name, limit in [("title", 120), ("description", 2000), ("location_note", 200)]:
            with self.subTest(field=name):
                form = ReportForm({**valid, name: "x" * (limit + 1)})
                self.assertFalse(form.is_valid())
                self.assertIn(name, form.errors)

class ReportViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="reporter", password="Report-test-2026!"
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_invalid_post_preserves_input(self):
        response = self.client.post(reverse("reporting:create"), {"title": "Sampah dekat halte"})
        self.assertContains(response, "Sampah dekat halte")
        self.assertContains(response, "Bagian ini wajib diisi.")
        self.assertIsNone(response.context["preview"])

    def test_preview_escapes_input_and_does_not_persist(self):
        url = reverse("reporting:create")
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(url, {
                "title": "  Sampah halte  ", "description": '<script>alert("x")</script>',
            })
        self.assertFalse(any(
            q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
            for q in queries
        ))
        self.assertEqual(response.context["preview"]["title"], "Sampah halte")
        self.assertContains(response, "PREVIEW · BELUM DISIMPAN")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertIsNone(self.client.get(url).context["preview"])

    def test_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        url = reverse("reporting:create")
        self.assertEqual(client.post(url, {}).status_code, 403)
        self.assertEqual(client.get(url).status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post(url, {
            "csrfmiddlewaretoken": token, "title": "Sampah", "description": "Di halte",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["preview"])

    def test_guests_are_sent_to_login(self):
        self.client.logout()
        for method in (self.client.get, self.client.post):
            with self.subTest(method=method.__name__):
                response = method(reverse("reporting:create"))
                self.assertRedirects(response, "/login/?next=/reporting/create/")

    def test_shared_navigation_links_to_reporting(self):
        for name in ("dashboard", "reporting:create"):
            response = self.client.get(reverse(name))
            self.assertTemplateUsed(response, "topbar.html")
            self.assertContains(response, 'href="/reporting/create/"', count=3 if name == "dashboard" else 2)
            self.assertContains(response, 'aria-controls="mobile-menu"')
            self.assertNotContains(response, "reporting/reporting.css")

    def test_login_returns_to_reporting(self):
        self.client.logout()
        url = reverse("login_user") + "?next=/reporting/create/"
        self.assertContains(self.client.get(url), 'name="next" value="/reporting/create/"')
        response = self.client.post(reverse("login_user"), {
            "username": "reporter", "password": "Report-test-2026!", "next": "/reporting/create/",
        })
        self.assertRedirects(response, reverse("reporting:create"))

    def test_login_rejects_external_redirects(self):
        for target in ("https://example.org/", "//example.org/", "javascript:alert(1)"):
            with self.subTest(target=target):
                self.client.logout()
                response = self.client.post(reverse("login_user"), {
                    "username": "reporter", "password": "Report-test-2026!", "next": target,
                })
                self.assertRedirects(response, reverse("dashboard"))

    def test_register_login_dashboard_flow(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("register_user")).status_code, 200)
        response = self.client.post(reverse("register_user"), {
            "username": "new-reporter", "password1": "Another-test-2026!", "password2": "Another-test-2026!",
        })
        self.assertRedirects(response, reverse("login_user"))
        response = self.client.post(reverse("login_user"), {
            "username": "new-reporter", "password": "Another-test-2026!",
        })
        self.assertRedirects(response, reverse("dashboard"))
