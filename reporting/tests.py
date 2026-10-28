from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import Client, SimpleTestCase, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.translation import override
from django.utils import timezone

from .forms import ReportForm
from .models import Report

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
        self.assertEqual(client.post(url, {"action": "save", **COORDINATES, "title": "Sampah", "description": "Di halte"}).status_code, 403)
        self.assertFalse(Report.objects.exists())
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
        for name in ("dashboard", "reporting:create", "reporting:list"):
            response = self.client.get(reverse(name))
            self.assertTemplateUsed(response, "topbar.html")
            self.assertContains(response, 'href="/reporting/"')
            if name == "dashboard":
                self.assertNotContains(response, 'href="/reporting/create/"')
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


class ReportHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner")
        cls.other = get_user_model().objects.create_user(username="other")

    def setUp(self):
        self.client.force_login(self.owner)
        self.data = {"title": "Sampah dekat halte", "description": "Plastik berserakan.", **COORDINATES}

    def test_empty_history_links_to_create_form(self):
        response = self.client.get(reverse("reporting:list"))
        self.assertContains(response, "Belum ada laporan")
        self.assertContains(response, 'href="/reporting/create/"')
        self.assertNotContains(response, 'id="id_title"')

    def test_save_uses_authenticated_owner_and_persists_after_refresh(self):
        before = timezone.now()
        token = self.client.get(reverse("reporting:create")).context["submission_token"]
        response = self.client.post(reverse("reporting:create"), {
            **self.data, "action": "save", "reporter": self.other.pk,
            "submission_token": token,
            "created_at": "2000-01-01T00:00:00Z", "location_note": "Di depan gerbang",
        })
        self.assertRedirects(response, reverse("reporting:list"))
        report = Report.objects.get()
        self.assertEqual(report.reporter, self.owner)
        self.assertGreaterEqual(report.created_at, before)
        self.assertEqual(report.title, self.data["title"])
        self.assertEqual(report.description, self.data["description"])
        self.assertEqual(report.location_note, "Di depan gerbang")
        self.assertEqual(report.latitude, Decimal(COORDINATES["latitude"]))
        self.assertEqual(report.longitude, Decimal(COORDINATES["longitude"]))
        for _ in range(2):
            history = self.client.get(reverse("reporting:list"))
            self.assertContains(history, self.data["title"])
            self.assertContains(history, "WIB")
        self.assertEqual(Report.objects.count(), 1)

    def test_preview_and_invalid_save_never_create_reports(self):
        preview = self.client.post(reverse("reporting:create"), {**self.data, "action": "preview"})
        self.assertIsNotNone(preview.context["preview"])
        for changes in ({"description": " "}, {"latitude": "91"}, {"longitude": ""}):
            response = self.client.post(reverse("reporting:create"), {**self.data, "action": "save", **changes})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
            self.assertIsNone(response.context["preview"])
        self.assertFalse(Report.objects.exists())

    def test_repeated_submission_only_saves_once(self):
        url = reverse("reporting:create")
        response = self.client.get(url)
        data = {**self.data, "action": "save", "submission_token": response.context["submission_token"]}
        self.assertRedirects(self.client.post(url, data), reverse("reporting:list"))
        first = Report.objects.first()
        original_time = first.created_at
        self.assertRedirects(self.client.post(url, data), reverse("reporting:list"))
        self.assertEqual(Report.objects.count(), 1)
        first.refresh_from_db()
        self.assertEqual(first.title, self.data["title"])
        self.assertEqual(first.created_at, original_time)

    def test_preview_and_validation_error_keep_the_same_submission(self):
        url = reverse("reporting:create")
        token = self.client.get(url).context["submission_token"]
        invalid = self.client.post(url, {**self.data, "action": "save", "submission_token": token, "latitude": "91"})
        self.assertFalse(Report.objects.exists())
        self.assertEqual(invalid.context["submission_token"], token)
        preview = self.client.post(url, {**self.data, "action": "preview", "submission_token": token})
        self.assertFalse(Report.objects.exists())
        self.assertEqual(preview.context["submission_token"], token)
        self.assertRedirects(self.client.post(url, {**self.data, "action": "save", "submission_token": token}), reverse("reporting:list"))
        self.assertEqual(Report.objects.count(), 1)

    def test_new_forms_can_create_distinct_reports_with_identical_details(self):
        url = reverse("reporting:create")
        tokens = [self.client.get(url).context["submission_token"] for _ in range(2)]
        self.assertNotEqual(*tokens)
        for token in tokens:
            self.assertRedirects(self.client.post(url, {**self.data, "action": "save", "submission_token": token}), reverse("reporting:list"))
        self.assertEqual(Report.objects.count(), 2)

    def test_invalid_or_other_users_submission_token_does_not_save(self):
        url = reverse("reporting:create")
        self.client.force_login(self.other)
        other_token = self.client.get(url).context["submission_token"]
        self.client.force_login(self.owner)
        for token in ("", "not-a-token", other_token):
            with self.subTest(token=token):
                response = self.client.post(url, {**self.data, "action": "save", "submission_token": token})
                self.assertContains(response, "Form perlu diperbarui")
                self.assertEqual(response.context["form"]["title"].value(), self.data["title"])
                self.assertFalse(Report.objects.exists())
        renewed = response.context["submission_token"]
        self.assertRedirects(self.client.post(url, {**self.data, "action": "save", "submission_token": renewed}), reverse("reporting:list"))

    def test_back_button_edits_do_not_overwrite_an_already_saved_report(self):
        url = reverse("reporting:create")
        token = self.client.get(url).context["submission_token"]
        self.client.post(url, {**self.data, "action": "save", "submission_token": token})
        changed = {**self.data, "title": "Laporan lain", "action": "save", "submission_token": token}
        response = self.client.post(url, changed)
        self.assertContains(response, "sebagai laporan baru")
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.get().title, self.data["title"])
        changed["submission_token"] = response.context["submission_token"]
        self.assertRedirects(self.client.post(url, changed), reverse("reporting:list"))
        self.assertEqual(Report.objects.count(), 2)

    def test_submission_id_is_unique_at_database_level(self):
        submission_id = uuid4()
        Report.objects.create(reporter=self.owner, submission_id=submission_id, **self.data)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Report.objects.create(reporter=self.owner, submission_id=submission_id, **self.data)
        self.assertEqual(Report.objects.count(), 1)

    def test_creation_time_is_shown_in_wib_across_midnight(self):
        report = Report.objects.create(reporter=self.owner, **self.data)
        utc_time = datetime(2026, 10, 27, 19, 5, tzinfo=datetime_timezone.utc)
        Report.objects.filter(pk=report.pk).update(created_at=utc_time)
        with override("en-us"):
            response = self.client.get(reverse("reporting:list"))
        self.assertContains(response, "28 Oct 2026, 02:05 WIB")
        self.assertContains(response, 'datetime="2026-10-28T02:05:00+07:00"')

    def test_history_is_private_even_with_other_user_query(self):
        mine = Report.objects.create(reporter=self.owner, **self.data)
        other = Report.objects.create(reporter=self.other, **{**self.data, "title": "Laporan rahasia akun lain"})
        response = self.client.get(reverse("reporting:list"), {"reporter": self.other.pk})
        self.assertEqual(list(response.context["page_obj"]), [mine])
        self.assertNotContains(response, other.title)
        self.client.force_login(self.other)
        response = self.client.get(reverse("reporting:list"))
        self.assertEqual(list(response.context["page_obj"]), [other])
        self.assertNotContains(response, mine.title)

    def test_history_orders_newest_first_and_paginates(self):
        reports = [Report.objects.create(reporter=self.owner, **{**self.data, "title": f"Laporan {i}"}) for i in range(11)]
        Report.objects.filter(pk=reports[0].pk).update(created_at=timezone.now() + timedelta(days=1))
        response = self.client.get(reverse("reporting:list"))
        page = response.context["page_obj"]
        self.assertEqual(page.paginator.count, 11)
        self.assertEqual(len(page), 10)
        self.assertEqual(list(page)[0], reports[0])
        self.assertContains(response, "Berikutnya")
        second = self.client.get(reverse("reporting:list"), {"page": 2}).context["page_obj"]
        self.assertEqual(len(second), 1)
        self.assertEqual(self.client.get(reverse("reporting:list"), {"page": "invalid"}).status_code, 200)

    def test_history_escapes_saved_text(self):
        Report.objects.create(reporter=self.owner, **{
            **self.data, "title": '<script>alert("test")</script>', "description": '<img src=x onerror="alert(1)">',
        })
        response = self.client.get(reverse("reporting:list"))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("test")</script>')
        self.assertNotContains(response, '<img src=x')

    def test_guests_cannot_read_history_or_save(self):
        self.client.logout()
        self.assertRedirects(self.client.get(reverse("reporting:list")), "/login/?next=/reporting/")
        self.assertRedirects(self.client.post(reverse("reporting:create"), {**self.data, "action": "save"}), "/login/?next=/reporting/create/")
        self.assertFalse(Report.objects.exists())

    def test_posting_to_history_cannot_create_reports(self):
        response = self.client.post(reverse("reporting:list"), {**self.data, "action": "save"})
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Report.objects.exists())


class ReportJSONTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="map-owner")
        cls.other = get_user_model().objects.create_user(username="map-other")

    def setUp(self):
        self.client.force_login(self.owner)
        self.url = reverse("reporting:show_json")
        self.data = {
            "title": "Sampah dekat halte", "description": "Plastik berserakan.",
            "location_note": "Dekat gerbang", **COORDINATES,
        }

    def test_guests_receive_json_error_instead_of_login_html(self):
        Report.objects.create(reporter=self.owner, **self.data)
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Silakan login untuk melihat laporan."})
        self.assertNotIn("Location", response)
        self.assertIn("no-store", response["Cache-Control"])

    def test_empty_map_returns_empty_array(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"reports": []})
        self.assertIn("no-store", response["Cache-Control"])

    def test_map_shares_report_details_without_account_or_submission_fields(self):
        mine = Report.objects.create(reporter=self.owner, submission_id=uuid4(), **self.data)
        other = Report.objects.create(reporter=self.other, **{**self.data, "title": "Laporan akun lain"})
        timestamp = datetime(2026, 10, 27, 19, 5, tzinfo=datetime_timezone.utc)
        Report.objects.filter(pk=mine.pk).update(created_at=timestamp)
        Report.objects.filter(pk=other.pk).update(created_at=timestamp + timedelta(minutes=1))
        with override("de"):
            payload = self.client.get(self.url).json()
        self.assertEqual(set(payload), {"reports"})
        self.assertEqual([row["id"] for row in payload["reports"]], [other.pk, mine.pk])
        self.assertEqual(payload["reports"][1], {
            "id": mine.pk, "title": self.data["title"],
            "description": self.data["description"], "location_note": self.data["location_note"],
            "latitude": -6.362, "longitude": 106.827,
            "created_at": "2026-10-27T19:05:00+00:00",
        })
        history = self.client.get(reverse("reporting:list"))
        self.assertEqual(list(history.context["page_obj"]), [mine])

    def test_map_includes_more_than_one_history_page_and_numeric_boundaries(self):
        coordinates = [("0", "0"), ("-90", "-180"), ("90", "180"), ("-6.123456", "106.654321")]
        for lat, lng in coordinates + [("1", "2")] * 7:
            Report.objects.create(reporter=self.owner, **{
                **self.data, "latitude": lat, "longitude": lng,
            })
        rows = self.client.get(self.url).json()["reports"]
        self.assertEqual(len(rows), 11)
        for row in rows:
            self.assertIsInstance(row["latitude"], (int, float))
            self.assertIsInstance(row["longitude"], (int, float))
        for lat, lng in coordinates:
            self.assertIn((float(lat), float(lng)), [(r["latitude"], r["longitude"]) for r in rows])

    def test_endpoint_cannot_write_reports(self):
        report = Report.objects.create(reporter=self.owner, **self.data)
        for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
            with self.subTest(method=method.__name__):
                response = method(self.url, {"title": "Diubah"})
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], "GET")
        report.refresh_from_db()
        self.assertEqual(report.title, self.data["title"])
        self.assertEqual(Report.objects.count(), 1)

    def test_saved_report_appears_once_but_preview_does_not(self):
        create_url = reverse("reporting:create")
        token = self.client.get(create_url).context["submission_token"]
        data = {**self.data, "submission_token": token}
        self.client.post(create_url, {**data, "action": "preview"})
        self.assertEqual(self.client.get(self.url).json(), {"reports": []})
        for _ in range(2):
            response = self.client.post(create_url, {**data, "action": "save"})
            self.assertRedirects(response, reverse("reporting:list"))
        rows = self.client.get(self.url).json()["reports"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], Report.objects.get().pk)
