from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client, SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.translation import override

from .forms import ReportForm

COORDINATES = {"latitude": "-6.362000", "longitude": "106.827000"}


class ReportFormTests(SimpleTestCase):
    def test_required_fields_reject_whitespace(self):
        form = ReportForm({**COORDINATES, "title": "   ", "description": "\n "})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"title", "description"})

    def test_limits_and_optional_location(self):
        valid = {**COORDINATES, "title": "a" * 120, "description": "b" * 2000}
        self.assertTrue(ReportForm(valid).is_valid())
        for name, limit in [("title", 120), ("description", 2000), ("location_note", 200)]:
            with self.subTest(field=name):
                form = ReportForm({**valid, name: "x" * (limit + 1)})
                self.assertFalse(form.is_valid())
                self.assertIn(name, form.errors)

    def test_location_must_be_explicit_and_complete(self):
        for coords in ({}, {"latitude": "-6"}, {"longitude": "106"}):
            with self.subTest(coords=coords):
                form = ReportForm({"title": "Sampah", "description": "Di halte", **coords})
                self.assertFalse(form.is_valid())
                self.assertIn("Pilih titik di peta", str(form.errors))

    def test_coordinate_ranges_precision_and_non_numeric_values(self):
        data = {"title": "Sampah", "description": "Di halte", **COORDINATES}
        cases = [
            ("latitude", "90.000001"), ("latitude", "-90.000001"),
            ("longitude", "180.000001"), ("longitude", "-180.000001"),
            ("latitude", "-6.1234567"), ("longitude", "106.1234567"),
            ("latitude", "NaN"), ("longitude", "Infinity"),
            ("latitude", "<script>"), ("longitude", "bukan angka"),
        ]
        for name, value in cases:
            with self.subTest(field=name, value=value):
                form = ReportForm({**data, name: value})
                self.assertFalse(form.is_valid())
                self.assertIn(name, form.errors)

    def test_zero_and_boundary_coordinates_are_valid(self):
        for lat, lng in [("0", "0"), ("-90", "-180"), ("90", "180")]:
            with self.subTest(latitude=lat, longitude=lng):
                form = ReportForm({
                    "title": "Sampah", "description": "Di halte", "latitude": lat, "longitude": lng,
                })
                self.assertTrue(form.is_valid(), form.errors)


class ReportViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="reporter", password="Report-test-2026!"
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_invalid_post_preserves_input(self):
        response = self.client.post(reverse("reporting:create"), {**COORDINATES, "title": "Sampah dekat halte"})
        self.assertContains(response, "Sampah dekat halte")
        self.assertContains(response, "Bagian ini wajib diisi.")
        self.assertIsNone(response.context["preview"])
        self.assertEqual(response.context["form"]["latitude"].value(), COORDINATES["latitude"])
        self.assertEqual(response.context["form"]["longitude"].value(), COORDINATES["longitude"])

    def test_preview_escapes_input_and_does_not_persist(self):
        url = reverse("reporting:create")
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(url, {
                **COORDINATES,
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
            **COORDINATES,
            "csrfmiddlewaretoken": token, "title": "Sampah", "description": "Di halte",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["preview"])

    def test_new_form_has_no_location_preselected(self):
        response = self.client.get(reverse("reporting:create"))
        self.assertIsNone(response.context["form"]["latitude"].value())
        self.assertIsNone(response.context["form"]["longitude"].value())
        self.assertContains(response, 'id="report-map"')

    def test_invalid_coordinates_do_not_generate_preview(self):
        response = self.client.post(reverse("reporting:create"), {
            "title": "Sampah", "description": "Di halte", **COORDINATES, "latitude": "91",
        })
        self.assertIsNone(response.context["preview"])
        self.assertContains(response, "Koordinat maksimal 90.")
        self.assertNotContains(response, "Lihat titik di OpenStreetMap")

    def test_preview_coordinates_and_map_link_use_decimal_points(self):
        with override("de"):
            response = self.client.post(reverse("reporting:create"), {
                "title": "Sampah", "description": "Di halte", **COORDINATES,
            })
        self.assertContains(response, 'id="preview-latitude">-6.362000</span>')
        self.assertContains(response, 'id="preview-longitude">106.827000</span>')
        self.assertContains(response, "mlat=-6.362000&amp;mlon=106.827000")

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
