from django.test import Client, SimpleTestCase
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

    def test_invalid_post_preserves_input(self):
        response = self.client.post(reverse("reporting:create"), {"title": "Sampah dekat halte"})
        self.assertContains(response, "Sampah dekat halte")
        self.assertContains(response, "Bagian ini wajib diisi.")
        self.assertIsNone(response.context["preview"])

    def test_preview_escapes_input_and_does_not_persist(self):
        # SimpleTestCase forbids database queries, including accidental writes.
        url = reverse("reporting:create")
        response = self.client.post(url, {
            "title": "  Sampah halte  ", "description": '<script>alert("x")</script>',
        })
        self.assertEqual(response.context["preview"]["title"], "Sampah halte")
        self.assertContains(response, "PREVIEW · BELUM DISIMPAN")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("x")</script>')
        self.assertIsNone(self.client.get(url).context["preview"])

    def test_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        url = reverse("reporting:create")
        self.assertEqual(client.post(url, {}).status_code, 403)
        self.assertEqual(client.get(url).status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post(url, {
            "csrfmiddlewaretoken": token, "title": "Sampah", "description": "Di halte",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["preview"])
