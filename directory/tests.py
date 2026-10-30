from decimal import Decimal
import json
from unittest.mock import MagicMock, patch
from urllib.error import URLError
from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from directory.forms import WasteBankForm
from directory.models import WasteBank


class DirectoryTestMixin:
    def create_superuser(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="testpassword123",
        )
        self.client.force_login(user)
        return user

    def create_staff_user(self):
        user = get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            password="testpassword123",
        )
        group, _ = Group.objects.get_or_create(name="Staff")
        group.user_set.add(user)
        self.client.force_login(user)
        return user

    def valid_bank_data(self, **overrides):
        data = {
            "name": "Bank Hijau",
            "address": "Jakarta Selatan",
            "contact_number": "08123456789",
            "email": "hijau@example.com",
            "latitude": "-6.200000",
            "longitude": "106.816666",
        }
        data.update(overrides)
        return data


class MainTest(DirectoryTestMixin, TestCase):
    def setUp(self):
        self.wastebank = WasteBank.objects.create(
            name="TPA UI",
            address="Depok",
            contact_number="08123123",
            email="tpaui@gmail.com",
        )

    def test_directory_url_is_accessible(self):
        response = self.client.get(reverse("directory:show_directory"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "directory/directory_page.html")
        self.assertContains(response, f'href="{reverse("dashboard")}"')

    def test_directory_preserves_trimmed_search_query(self):
        response = self.client.get(
            reverse("directory:show_directory"), {"name": "  Depok  "}
        )

        self.assertEqual(response.context["name_query"], "Depok")
        self.assertContains(response, 'value="Depok"')

    def test_directory_hides_staff_controls_for_anonymous_users(self):
        response = self.client.get(reverse("directory:show_directory"))

        self.assertContains(response, 'data-can-edit="false"')
        self.assertContains(response, 'data-can-delete="false"')
        self.assertNotContains(response, "Tambahkan lokasi baru")
        self.assertNotContains(response, "Perbarui data dari OpenStreetMap")

    def test_directory_shows_edit_controls_for_staff(self):
        staff = get_user_model().objects.create_user(username="directory-staff")
        group = Group.objects.create(name="Staff")
        group.user_set.add(staff)
        self.client.force_login(staff)

        response = self.client.get(reverse("directory:show_directory"))

        self.assertContains(response, 'data-can-edit="true"')
        self.assertContains(response, 'data-can-delete="false"')
        self.assertContains(response, "Tambahkan lokasi baru")
        self.assertContains(response, "Perbarui data dari OpenStreetMap")

    def test_directory_shows_all_controls_for_a_superuser(self):
        self.create_superuser()

        response = self.client.get(reverse("directory:show_directory"))

        self.assertContains(response, 'data-can-edit="true"')
        self.assertContains(response, 'data-can-delete="true"')
        self.assertContains(response, "Perbarui data dari OpenStreetMap")

    def test_undefined_link_returns_404(self):
        response = self.client.get("/hide_directory/")

        self.assertEqual(response.status_code, 404)

    def test_empty_directory_page_still_loads_and_api_is_empty(self):
        WasteBank.objects.all().delete()

        page_response = self.client.get(reverse("directory:show_directory"))
        api_response = self.client.get(reverse("directory:get_waste_bank_json"))

        self.assertEqual(page_response.status_code, 200)
        self.assertEqual(api_response.json(), [])

    def test_display_wastebank_form(self):
        self.create_superuser()
        response = self.client.get(reverse("directory:create_waste_bank"))

        self.assertTemplateUsed(response, "directory/waste_bank_form.html")
        for label in ("Nama", "Alamat", "Nomor Kontak", "Email", "Latitude", "Longitude"):
            self.assertContains(response, label)


class WasteBankApiTests(TestCase):
    def setUp(self):
        self.wastebank = WasteBank.objects.create(
            name="TPA UI",
            address="Depok",
            contact_number="08123123",
            email="tpaui@gmail.com",
            latitude=Decimal("-6.360000"),
            longitude=Decimal("106.830000"),
        )

    def test_json_endpoint_returns_all_fields(self):
        response = self.client.get(reverse("directory:get_waste_bank_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(),
            [{
                "pk": str(self.wastebank.pk),
                "source": "manual",
                "is_manual": True,
                "fields": {
                    "name": "TPA UI",
                    "address": "Depok",
                    "contact_number": "08123123",
                    "email": "tpaui@gmail.com",
                    "latitude": "-6.360000",
                    "longitude": "106.830000",
                },
            }],
        )

    def test_json_endpoint_filters_by_name_address_contact_and_email(self):
        for query in ("tpa", "depok", "08123123", "tpaui@gmail.com"):
            with self.subTest(query=query):
                response = self.client.get(
                    reverse("directory:get_waste_bank_json"),
                    {"name": f"  {query}  "},
                )
                self.assertEqual(len(response.json()), 1)

    def test_json_endpoint_returns_no_match_for_unknown_search(self):
        response = self.client.get(
            reverse("directory:get_waste_bank_json"), {"name": "unknown"}
        )

        self.assertEqual(response.json(), [])

    def test_json_endpoint_serializes_optional_fields_as_null(self):
        bank = WasteBank.objects.create(
            name="Bank Tanpa Kontak", address="Bogor", contact_number=None, email=None
        )

        response = self.client.get(reverse("directory:get_waste_bank_json"))
        result = next(item for item in response.json() if item["pk"] == str(bank.pk))

        self.assertIsNone(result["fields"]["contact_number"])
        self.assertIsNone(result["fields"]["email"])

    def test_json_endpoint_includes_persisted_osm_locations_without_fetching(self):
        osm_bank = WasteBank.objects.create(
            name="Bank Sampah OSM",
            address="Jakarta",
            latitude=Decimal("-6.200000"),
            longitude=Decimal("106.816666"),
            is_osm=True,
        )
        with patch("directory.views.fetch_osm_waste_banks") as mock_fetch:
            response = self.client.get(reverse("directory:get_waste_bank_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["pk"], str(self.wastebank.pk))
        self.assertEqual(response.json()[1]["pk"], str(osm_bank.pk))
        self.assertEqual(response.json()[1]["source"], "osm")
        self.assertFalse(response.json()[1]["is_manual"])
        mock_fetch.assert_not_called()


class OsmWasteBankSyncTests(DirectoryTestMixin, TestCase):
    def setUp(self):
        self.sleep = patch("directory.views.time.sleep")
        self.sleep_mock = self.sleep.start()
        self.addCleanup(self.sleep.stop)

    @patch("directory.views.urlopen")
    def test_fetches_bank_sampah_from_nominatim_for_each_province(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
            {
                "name": "Bank Sampah Melati",
                "display_name": "Bank Sampah Melati, Depok, Jawa Barat, Indonesia",
                "lat": "-6.370246",
                "lon": "106.827516",
                "extratags": {"phone": "08123456789"},
            }
        ]).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        self.create_superuser()
        response = self.client.post(reverse("directory:sync_osm_waste_banks"))

        self.assertRedirects(response, reverse("directory:show_directory"))
        bank = WasteBank.objects.get(
            is_osm=True,
            latitude=Decimal("-6.370246"),
            longitude=Decimal("106.827516"),
        )
        self.assertEqual(bank.name, "Bank Sampah Melati")
        self.assertEqual(
            bank.address,
            "Bank Sampah Melati, Depok, Jawa Barat, Indonesia",
        )
        self.assertEqual(bank.contact_number, "08123456789")
        self.assertIsNone(bank.email)
        self.assertEqual(bank.latitude, Decimal("-6.370246"))
        self.assertEqual(bank.longitude, Decimal("106.827516"))
        requests = [call.args[0] for call in mock_urlopen.call_args_list]
        self.assertEqual(len(requests), 5)
        self.assertTrue(all(
            request.full_url.startswith(
                "https://nominatim.openstreetmap.org/search?"
            )
            for request in requests
        ))
        queries = [
            parse_qs(request.full_url.split("?", 1)[1])
            for request in requests
        ]
        self.assertEqual(
            [query["q"][0] for query in queries],
            [
                "bank sampah, Jawa Barat, Indonesia",
                "bank sampah, Jawa Tengah, Indonesia",
                "bank sampah, Jawa Timur, Indonesia",
                "bank sampah, Daerah Istimewa Yogyakarta, Indonesia",
                "bank sampah, Banten, Indonesia",
            ],
        )
        self.assertTrue(all(query["countrycodes"] == ["id"] for query in queries))
        self.assertTrue(all(query["limit"] == ["40"] for query in queries))
        self.assertEqual(mock_urlopen.call_args.kwargs["timeout"], 5)
        self.assertEqual(self.sleep_mock.call_count, 4)

    @patch("directory.views.urlopen")
    def test_sync_updates_existing_osm_records_without_duplicates(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([
                {
                    "name": "Updated Bank Sampah",
                    "display_name": "Updated Bank Sampah, Depok",
                    "lat": "-6.370246",
                    "lon": "106.827516",
                }
            ]).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        existing_bank = WasteBank.objects.create(
            name="Old Name",
            address="Old address",
            latitude=Decimal("-6.370246"),
            longitude=Decimal("106.827516"),
            is_osm=True,
        )
        stale_osm_bank = WasteBank.objects.create(
            name="No Longer In OSM",
            address="Old location",
            latitude=Decimal("-6.500000"),
            longitude=Decimal("107.000000"),
            is_osm=True,
        )
        manual_bank = WasteBank.objects.create(
            name="Manually Added",
            address="Keep this location",
        )
        self.create_staff_user()

        response = self.client.post(reverse("directory:sync_osm_waste_banks"))

        self.assertRedirects(response, reverse("directory:show_directory"))
        self.assertFalse(WasteBank.objects.filter(pk=existing_bank.pk).exists())
        self.assertFalse(WasteBank.objects.filter(pk=stale_osm_bank.pk).exists())
        self.assertTrue(WasteBank.objects.filter(pk=manual_bank.pk, is_osm=False).exists())
        self.assertTrue(
            WasteBank.objects.filter(
                name="Updated Bank Sampah",
                is_osm=True,
                latitude=Decimal("-6.370246"),
                longitude=Decimal("106.827516"),
            ).exists()
        )
        self.assertEqual(
            WasteBank.objects.filter(is_osm=True).count(),
            1,
        )

    @patch("directory.views.urlopen")
    def test_successful_empty_sync_clears_only_osm_records(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps([]).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        osm_bank = WasteBank.objects.create(
            name="Old OSM Location",
            address="Old location",
            is_osm=True,
        )
        manual_bank = WasteBank.objects.create(
            name="Manual Location",
            address="Keep this location",
        )
        self.create_superuser()

        response = self.client.post(reverse("directory:sync_osm_waste_banks"))

        self.assertRedirects(response, reverse("directory:show_directory"))
        self.assertFalse(WasteBank.objects.filter(pk=osm_bank.pk).exists())
        self.assertTrue(WasteBank.objects.filter(pk=manual_bank.pk).exists())
        self.assertFalse(WasteBank.objects.filter(is_osm=True).exists())

    @patch("directory.views.urlopen", side_effect=URLError("OSM unavailable"))
    def test_osm_failure_reports_an_error_without_changing_database(self, mock_urlopen):
        self.create_superuser()
        bank = WasteBank.objects.create(name="Bank Lokal", address="Jakarta")
        osm_bank = WasteBank.objects.create(
            name="Existing OSM Location",
            address="Keep until successful sync",
            is_osm=True,
        )

        response = self.client.post(
            reverse("directory:sync_osm_waste_banks"), follow=True
        )

        self.assertEqual(WasteBank.objects.count(), 2)
        self.assertTrue(WasteBank.objects.filter(pk=bank.pk).exists())
        self.assertTrue(WasteBank.objects.filter(pk=osm_bank.pk).exists())
        self.assertContains(response, "Gagal mengambil data bank sampah")
        mock_urlopen.assert_called_once()

    @patch("directory.views.urlopen")
    def test_unexpected_nominatim_response_does_not_clear_existing_osm_data(
        self, mock_urlopen
    ):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "error": "Search failed",
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        self.create_superuser()
        osm_bank = WasteBank.objects.create(
            name="Existing OSM Location",
            address="Keep until successful sync",
            is_osm=True,
        )

        response = self.client.post(
            reverse("directory:sync_osm_waste_banks"), follow=True
        )

        self.assertTrue(WasteBank.objects.filter(pk=osm_bank.pk).exists())
        self.assertContains(response, "Gagal mengambil data bank sampah")

    def test_sync_requires_staff_or_superuser(self):
        user = get_user_model().objects.create_user(username="regular-sync")
        self.client.force_login(user)

        response = self.client.post(reverse("directory:sync_osm_waste_banks"))

        self.assertEqual(response.status_code, 403)

    def test_sync_requires_post(self):
        self.create_superuser()

        response = self.client.get(reverse("directory:sync_osm_waste_banks"))

        self.assertEqual(response.status_code, 405)


class WasteBankManagementTests(DirectoryTestMixin, TestCase):
    def setUp(self):
        self.wastebank = WasteBank.objects.create(
            name="TPA UI",
            address="Depok",
            contact_number="08123123",
            email="tpaui@gmail.com",
        )

    def test_create_requires_login(self):
        response = self.client.get(reverse("directory:create_waste_bank"))

        self.assertRedirects(
            response,
            f"/login/?next={reverse('directory:create_waste_bank')}",
        )

    def test_create_rejects_regular_authenticated_user(self):
        user = get_user_model().objects.create_user(username="regular")
        self.client.force_login(user)

        response = self.client.get(reverse("directory:create_waste_bank"))

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_create_a_waste_bank(self):
        self.create_superuser()

        response = self.client.post(
            reverse("directory:create_waste_bank"), self.valid_bank_data()
        )

        self.assertRedirects(response, reverse("directory:show_directory"))
        self.assertTrue(WasteBank.objects.filter(name="Bank Hijau").exists())

    def test_create_renders_validation_errors_without_saving(self):
        self.create_superuser()

        response = self.client.post(
            reverse("directory:create_waste_bank"),
            self.valid_bank_data(name="", email="invalid"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        self.assertIn("email", response.context["form"].errors)
        self.assertEqual(WasteBank.objects.count(), 1)

    def test_edit_requires_login(self):
        response = self.client.get(
            reverse("directory:edit_waste_bank", args=[self.wastebank.pk])
        )

        self.assertRedirects(
            response,
            f"/login/?next={reverse('directory:edit_waste_bank', args=[self.wastebank.pk])}",
        )

    def test_staff_can_display_and_update_a_waste_bank(self):
        self.create_staff_user()

        get_response = self.client.get(
            reverse("directory:edit_waste_bank", args=[self.wastebank.pk])
        )
        post_response = self.client.post(
            reverse("directory:edit_waste_bank", args=[self.wastebank.pk]),
            self.valid_bank_data(name="Updated TPA"),
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Perbarui Bank Sampah")
        self.assertRedirects(post_response, reverse("directory:show_directory"))
        self.wastebank.refresh_from_db()
        self.assertEqual(self.wastebank.name, "Updated TPA")

    def test_superuser_can_edit_a_waste_bank(self):
        self.create_superuser()

        response = self.client.post(
            reverse("directory:edit_waste_bank", args=[self.wastebank.pk]),
            self.valid_bank_data(name="Superuser Updated"),
        )

        self.assertRedirects(response, reverse("directory:show_directory"))
        self.wastebank.refresh_from_db()
        self.assertEqual(self.wastebank.name, "Superuser Updated")

    def test_edit_rejects_regular_authenticated_user(self):
        user = get_user_model().objects.create_user(username="regular-editor")
        self.client.force_login(user)

        response = self.client.get(
            reverse("directory:edit_waste_bank", args=[self.wastebank.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_edit_renders_coordinate_validation_errors_without_saving(self):
        self.create_superuser()

        response = self.client.post(
            reverse("directory:edit_waste_bank", args=[self.wastebank.pk]),
            self.valid_bank_data(latitude="91", longitude="181"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("latitude", response.context["form"].errors)
        self.assertIn("longitude", response.context["form"].errors)
        self.wastebank.refresh_from_db()
        self.assertEqual(self.wastebank.name, "TPA UI")

    def test_edit_returns_404_for_unknown_bank(self):
        self.create_superuser()

        response = self.client.get(
            reverse(
                "directory:edit_waste_bank",
                args=["00000000-0000-0000-0000-000000000000"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_delete_requires_login(self):
        response = self.client.post(
            reverse("directory:delete_waste_bank", args=[self.wastebank.pk])
        )

        self.assertRedirects(
            response,
            f"/login/?next={reverse('directory:delete_waste_bank', args=[self.wastebank.pk])}",
        )

    def test_staff_cannot_delete_a_waste_bank(self):
        self.create_staff_user()

        response = self.client.post(
            reverse("directory:delete_waste_bank", args=[self.wastebank.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(WasteBank.objects.filter(pk=self.wastebank.pk).exists())

    def test_superuser_get_delete_url_does_not_delete_the_bank(self):
        self.create_superuser()

        response = self.client.get(
            reverse("directory:delete_waste_bank", args=[self.wastebank.pk])
        )

        self.assertRedirects(response, reverse("directory:show_directory"))
        self.assertTrue(WasteBank.objects.filter(pk=self.wastebank.pk).exists())

    def test_superuser_can_delete_a_waste_bank_with_post(self):
        self.create_superuser()

        response = self.client.post(
            reverse("directory:delete_waste_bank", args=[self.wastebank.pk])
        )

        self.assertRedirects(response, reverse("directory:show_directory"))
        self.assertFalse(WasteBank.objects.filter(pk=self.wastebank.pk).exists())

    def test_delete_returns_404_for_unknown_bank(self):
        self.create_superuser()

        response = self.client.post(
            reverse(
                "directory:delete_waste_bank",
                args=["00000000-0000-0000-0000-000000000000"],
            )
        )

        self.assertEqual(response.status_code, 404)


class CreateWasteBankAjaxTests(DirectoryTestMixin, TestCase):
    def test_ajax_endpoint_only_accepts_post(self):
        response = self.client.get(reverse("directory:create_waste_bank_ajax"))

        self.assertEqual(response.status_code, 405)

    def test_ajax_endpoint_rejects_an_unauthorized_user(self):
        response = self.client.post(
            reverse("directory:create_waste_bank_ajax"), self.valid_bank_data()
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json(), {"message": "Hanya staf yang dapat menambahkan lokasi."}
        )

    def test_staff_can_create_a_waste_bank_with_ajax(self):
        self.create_staff_user()

        response = self.client.post(
            reverse("directory:create_waste_bank_ajax"), self.valid_bank_data()
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["message"], "Lokasi berhasil ditambahkan.")
        self.assertTrue(WasteBank.objects.filter(pk=body["pk"], name="Bank Hijau").exists())

    def test_superuser_can_create_a_waste_bank_with_ajax(self):
        self.create_superuser()

        response = self.client.post(
            reverse("directory:create_waste_bank_ajax"),
            self.valid_bank_data(name="Superuser Bank"),
        )

        self.assertEqual(response.status_code, 201)

    def test_ajax_endpoint_returns_form_errors_for_invalid_data(self):
        self.create_staff_user()

        response = self.client.post(
            reverse("directory:create_waste_bank_ajax"),
            self.valid_bank_data(name="", longitude="181"),
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("name", errors)
        self.assertIn("longitude", errors)
        self.assertEqual(WasteBank.objects.count(), 0)


class WasteBankFormAndModelTests(TestCase):
    def test_form_accepts_valid_data(self):
        form = WasteBankForm(data={
            "name": "Bank Valid",
            "address": "Bandung",
            "contact_number": "081234567890",
            "email": "valid@example.com",
            "latitude": "-6.900000",
            "longitude": "107.600000",
        })

        self.assertTrue(form.is_valid())

    def test_form_accepts_blank_optional_contact_data(self):
        form = WasteBankForm(data={
            "name": "Bank Tanpa Kontak",
            "address": "Bandung",
            "contact_number": "",
            "email": "",
            "latitude": "-6.900000",
            "longitude": "107.600000",
        })

        self.assertTrue(form.is_valid())

    def test_form_metadata_contains_labels_and_widgets(self):
        form = WasteBankForm()

        self.assertEqual(form.fields["name"].label, "Nama Bank Sampah")
        self.assertEqual(form.fields["address"].widget.attrs["rows"], 3)
        self.assertEqual(form.fields["email"].widget.input_type, "email")
        self.assertEqual(form.fields["latitude"].widget.attrs["step"], "0.000001")

    def test_form_rejects_coordinates_outside_allowed_ranges(self):
        form = WasteBankForm(data={
            "name": "Bank Invalid",
            "address": "Bandung",
            "contact_number": "081234567890",
            "email": "valid@example.com",
            "latitude": "-91",
            "longitude": "181",
        })

        self.assertFalse(form.is_valid())
        self.assertIn("latitude", form.errors)
        self.assertIn("longitude", form.errors)

    def test_model_string_representation_and_coordinate_defaults(self):
        bank = WasteBank.objects.create(name="Community Bank", address="Depok")
        bank.refresh_from_db()

        self.assertEqual(str(bank), "Community Bank")
        self.assertEqual(bank.latitude, Decimal("-6.370246"))
        self.assertEqual(bank.longitude, Decimal("106.827516"))
