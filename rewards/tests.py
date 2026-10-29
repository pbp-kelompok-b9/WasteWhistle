from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rewards.models import Reward, PointTransaction, Redemption


User = get_user_model()


def data_hadiah(**kwargs):
    data = {
        "nama": "Voucher Baru",
        "deskripsi": "Deskripsi voucher baru.",
        "kategori": "belanja",
        "harga_poin": 100,
        "stok": 5,
        "gambar": "",
        "level_minimal": 1,
    }
    data.update(kwargs)
    return data


class RewardTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="warga", password="rahasia123")

        self.reward = Reward.objects.create(
            nama="Voucher Transportasi",
            deskripsi="Potongan tiket bus.",
            kategori="transportasi",
            harga_poin=100,
            stok=3,
            level_minimal=1,
        )
        self.reward_mahal = Reward.objects.create(
            nama="Tas Belanja Eco",
            deskripsi="Tas belanja ramah lingkungan.",
            kategori="belanja",
            harga_poin=500,
            stok=2,
            level_minimal=1,
        )
        self.reward_terkunci = Reward.objects.create(
            nama="Hadiah Level Tinggi",
            kategori="acara",
            harga_poin=50,
            stok=1,
            level_minimal=99,
        )

    def beri_poin(self, jumlah, referensi=""):
        return PointTransaction.objects.create(
            user=self.user, jumlah=jumlah, alasan="Poin awal", referensi=referensi
        )

    def login(self):
        self.client.login(username="warga", password="rahasia123")


class RewardModelTest(RewardTestBase):
    def test_reward_str(self):
        self.assertEqual(str(self.reward), "Voucher Transportasi")

    def test_reward_default_values(self):
        reward = Reward.objects.create(nama="Default", harga_poin=10)
        self.assertEqual(reward.kategori, "lainnya")
        self.assertEqual(reward.stok, 0)
        self.assertEqual(reward.level_minimal, 1)

    def test_reward_ordering_by_harga_poin(self):
        harga = list(Reward.objects.values_list("harga_poin", flat=True))
        self.assertEqual(harga, sorted(harga))

    def test_point_transaction_str(self):
        trx = self.beri_poin(50)
        self.assertIn("+50", str(trx))
        self.assertIn("Poin awal", str(trx))

    def test_redemption_str(self):
        redemption = Redemption.objects.create(
            user=self.user, reward=self.reward, poin_dipakai=100, kode="WW-ABC123"
        )
        self.assertEqual(str(redemption), f"{self.user} - Voucher Transportasi")

    def test_referensi_unik_per_user(self):
        from django.db import IntegrityError, transaction

        self.beri_poin(10, referensi="laporan-1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.beri_poin(10, referensi="laporan-1")

    def test_referensi_kosong_boleh_duplikat(self):
        self.beri_poin(10)
        self.beri_poin(10)
        self.assertEqual(PointTransaction.objects.filter(user=self.user).count(), 2)


class RewardListPageTest(RewardTestBase):
    def test_reward_list_is_accessible(self):
        response = self.client.get(reverse("rewards:reward_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "rewards/reward_list.html")
        self.assertContains(response, "Rewards")
        self.assertNotContains(response, "Tambah hadiah")

    def test_reward_list_kategori_valid_dipertahankan(self):
        response = self.client.get(reverse("rewards:reward_list"), {"kategori": "belanja"})

        self.assertEqual(response.context["kategori_aktif"], "belanja")

    def test_reward_list_kategori_tidak_valid_dikosongkan(self):
        response = self.client.get(reverse("rewards:reward_list"), {"kategori": "ngawur"})

        self.assertEqual(response.context["kategori_aktif"], "")

    def test_reward_list_maks_poin_bukan_angka_dikosongkan(self):
        response = self.client.get(reverse("rewards:reward_list"), {"maks_poin": "abc"})

        self.assertEqual(response.context["maks_poin"], "")

    def test_reward_list_maks_poin_angka_dipertahankan(self):
        response = self.client.get(reverse("rewards:reward_list"), {"maks_poin": "300"})

        self.assertEqual(response.context["maks_poin"], "300")

    @patch("rewards.views.is_petugas", return_value=True)
    def test_reward_list_petugas_melihat_tombol_tambah(self, _):
        response = self.client.get(reverse("rewards:reward_list"))

        self.assertTrue(response.context["is_petugas"])
        self.assertIsNotNone(response.context["form"])
        self.assertContains(response, "Tambah hadiah")


class GetRewardsJsonTest(RewardTestBase):
    def test_get_rewards_json_returns_all(self):
        response = self.client.get(reverse("rewards:get_rewards_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    def test_get_rewards_json_struktur_data(self):
        response = self.client.get(reverse("rewards:get_rewards_json"))
        item = next(i for i in response.json() if i["pk"] == str(self.reward.pk))

        self.assertEqual(item["fields"]["nama"], "Voucher Transportasi")
        self.assertEqual(item["fields"]["kategori"], "transportasi")
        self.assertEqual(item["fields"]["kategori_label"], "Transportasi")
        self.assertEqual(item["fields"]["harga_poin"], 100)
        self.assertEqual(item["fields"]["stok"], 3)
        self.assertFalse(item["fields"]["terkunci"])

    def test_get_rewards_json_filter_kategori(self):
        response = self.client.get(reverse("rewards:get_rewards_json"), {"kategori": "belanja"})
        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["nama"], "Tas Belanja Eco")

    def test_get_rewards_json_kategori_tidak_valid_diabaikan(self):
        response = self.client.get(reverse("rewards:get_rewards_json"), {"kategori": "ngawur"})

        self.assertEqual(len(response.json()), 3)

    def test_get_rewards_json_filter_maks_poin(self):
        response = self.client.get(reverse("rewards:get_rewards_json"), {"maks_poin": "100"})
        harga = [i["fields"]["harga_poin"] for i in response.json()]

        self.assertTrue(all(h <= 100 for h in harga))
        self.assertEqual(len(harga), 2)

    def test_get_rewards_json_maks_poin_bukan_angka_diabaikan(self):
        response = self.client.get(reverse("rewards:get_rewards_json"), {"maks_poin": "abc"})

        self.assertEqual(len(response.json()), 3)

    def test_get_rewards_json_hadiah_level_tinggi_terkunci(self):
        response = self.client.get(reverse("rewards:get_rewards_json"))
        item = next(i for i in response.json() if i["pk"] == str(self.reward_terkunci.pk))

        self.assertTrue(item["fields"]["terkunci"])

    def test_get_rewards_json_hanya_get(self):
        response = self.client.post(reverse("rewards:get_rewards_json"))

        self.assertEqual(response.status_code, 405)


class GetMyRewardsJsonTest(RewardTestBase):
    def test_my_rewards_belum_login(self):
        response = self.client.get(reverse("rewards:get_my_rewards_json"))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data["authenticated"])
        self.assertEqual(data["total_poin"], 0)
        self.assertEqual(data["level"], 1)
        self.assertEqual(data["redemptions"], [])
        self.assertEqual(data["transaksi"], [])
        self.assertEqual(len(data["dots"]), 10)

    def test_my_rewards_sudah_login(self):
        self.login()
        self.beri_poin(250)
        Redemption.objects.create(
            user=self.user, reward=self.reward, poin_dipakai=100, kode="WW-ABC123"
        )

        response = self.client.get(reverse("rewards:get_my_rewards_json"))
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["authenticated"])
        self.assertEqual(len(data["redemptions"]), 1)
        self.assertEqual(data["redemptions"][0]["nama"], "Voucher Transportasi")
        self.assertEqual(data["redemptions"][0]["kode"], "WW-ABC123")
        self.assertEqual(data["redemptions"][0]["poin_dipakai"], 100)
        self.assertEqual(len(data["transaksi"]), 1)
        self.assertEqual(data["transaksi"][0]["jumlah"], 250)

    def test_my_rewards_tidak_menampilkan_data_user_lain(self):
        lain = User.objects.create_user(username="lain", password="rahasia123")
        PointTransaction.objects.create(user=lain, jumlah=100, alasan="Milik lain")
        Redemption.objects.create(user=lain, reward=self.reward, poin_dipakai=100)

        self.login()
        data = self.client.get(reverse("rewards:get_my_rewards_json")).json()

        self.assertEqual(data["redemptions"], [])
        self.assertEqual(data["transaksi"], [])

    def test_my_rewards_tidak_di_cache(self):
        response = self.client.get(reverse("rewards:get_my_rewards_json"))

        self.assertIn("no-cache", response["Cache-Control"])


class CreateRewardAjaxTest(RewardTestBase):
    def url(self):
        return reverse("rewards:create_reward_ajax")

    def test_create_reward_belum_login(self):
        response = self.client.post(self.url(), data_hadiah())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Reward.objects.count(), 3)

    def test_create_reward_bukan_petugas(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=False):
            response = self.client.post(self.url(), data_hadiah())

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Reward.objects.count(), 3)

    def test_create_reward_petugas_berhasil(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url(), data_hadiah())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reward.objects.count(), 4)
        self.assertTrue(Reward.objects.filter(nama="Voucher Baru").exists())
        self.assertIn("pk", response.json())

    def test_create_reward_data_tidak_valid(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url(), data_hadiah(nama="", harga_poin=""))

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertEqual(Reward.objects.count(), 3)

    def test_create_reward_hanya_post(self):
        response = self.client.get(self.url())

        self.assertEqual(response.status_code, 405)


class UpdateRewardAjaxTest(RewardTestBase):
    def url(self, pk=None):
        return reverse("rewards:update_reward_ajax", args=[pk or self.reward.pk])

    def test_update_reward_bukan_petugas(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=False):
            response = self.client.post(self.url(), data_hadiah(nama="Diubah"))

        self.assertEqual(response.status_code, 403)
        self.reward.refresh_from_db()
        self.assertEqual(self.reward.nama, "Voucher Transportasi")

    def test_update_reward_petugas_berhasil(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(
                self.url(), data_hadiah(nama="Voucher Diubah", harga_poin=150)
            )

        self.assertEqual(response.status_code, 200)
        self.reward.refresh_from_db()
        self.assertEqual(self.reward.nama, "Voucher Diubah")
        self.assertEqual(self.reward.harga_poin, 150)

    def test_update_reward_tidak_ditemukan(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url(pk=9999), data_hadiah())

        self.assertEqual(response.status_code, 404)

    def test_update_reward_data_tidak_valid(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url(), data_hadiah(nama=""))

        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.reward.refresh_from_db()
        self.assertEqual(self.reward.nama, "Voucher Transportasi")


class DeleteRewardAjaxTest(RewardTestBase):
    def url(self, pk=None):
        return reverse("rewards:delete_reward_ajax", args=[pk or self.reward.pk])

    def test_delete_reward_belum_login(self):
        response = self.client.post(self.url())

        self.assertEqual(response.status_code, 401)
        self.assertTrue(Reward.objects.filter(pk=self.reward.pk).exists())

    def test_delete_reward_bukan_petugas(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=False):
            response = self.client.post(self.url())

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Reward.objects.filter(pk=self.reward.pk).exists())

    def test_delete_reward_petugas_berhasil(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url())

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reward.objects.filter(pk=self.reward.pk).exists())
        self.assertIn("Voucher Transportasi", response.json()["message"])

    def test_delete_reward_tidak_ditemukan(self):
        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url(pk=9999))

        self.assertEqual(response.status_code, 404)

    def test_delete_reward_yang_sudah_ditukar_ditolak(self):
        Redemption.objects.create(user=self.user, reward=self.reward, poin_dipakai=100)

        self.login()
        with patch("rewards.views.is_petugas", return_value=True):
            response = self.client.post(self.url())

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Reward.objects.filter(pk=self.reward.pk).exists())


class RedeemRewardAjaxTest(RewardTestBase):
    def url(self, pk=None):
        return reverse("rewards:redeem_reward_ajax", args=[pk or self.reward.pk])

    def test_redeem_belum_login(self):
        response = self.client.post(self.url())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Redemption.objects.count(), 0)

    def test_redeem_hadiah_tidak_ditemukan(self):
        self.login()
        response = self.client.post(self.url(pk=9999))

        self.assertEqual(response.status_code, 404)

    def test_redeem_poin_tidak_cukup(self):
        self.login()
        self.beri_poin(50)
        response = self.client.post(self.url())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Poin kamu tidak cukup.")
        self.assertEqual(Redemption.objects.count(), 0)
        self.reward.refresh_from_db()
        self.assertEqual(self.reward.stok, 3)

    def test_redeem_stok_habis(self):
        self.login()
        self.beri_poin(1000)
        self.reward.stok = 0
        self.reward.save()
        response = self.client.post(self.url())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Stok hadiah habis.")
        self.assertEqual(Redemption.objects.count(), 0)

    def test_redeem_level_belum_cukup(self):
        self.login()
        self.beri_poin(1000)
        response = self.client.post(self.url(pk=self.reward_terkunci.pk))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Level kamu belum cukup untuk hadiah ini.")
        self.assertEqual(Redemption.objects.count(), 0)

    def test_redeem_berhasil(self):
        self.login()
        self.beri_poin(300)
        response = self.client.post(self.url())
        data = response.json()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(data["kode"].startswith("WW-"))
        self.assertEqual(len(data["kode"]), 9)
        self.assertIn(data["kode"], data["message"])

        redemption = Redemption.objects.get(user=self.user)
        self.assertEqual(redemption.reward, self.reward)
        self.assertEqual(redemption.poin_dipakai, 100)
        self.assertEqual(redemption.kode, data["kode"])

        self.reward.refresh_from_db()
        self.assertEqual(self.reward.stok, 2)

    def test_redeem_mencatat_transaksi_poin_negatif(self):
        self.login()
        self.beri_poin(300)
        self.client.post(self.url())

        redemption = Redemption.objects.get(user=self.user)
        trx = PointTransaction.objects.get(referensi=f"redeem-{redemption.pk}")
        self.assertEqual(trx.user, self.user)
        self.assertEqual(trx.jumlah, -100)
        self.assertEqual(trx.alasan, "Tukar: Voucher Transportasi")

    def test_redeem_tidak_bisa_dua_kali_dengan_poin_sama(self):
        self.login()
        self.beri_poin(150)

        pertama = self.client.post(self.url())
        kedua = self.client.post(self.url())

        self.assertEqual(pertama.status_code, 201)
        self.assertEqual(kedua.status_code, 400)
        self.assertEqual(Redemption.objects.filter(user=self.user).count(), 1)

    def test_redeem_hanya_post(self):
        self.login()
        response = self.client.get(self.url())

        self.assertEqual(response.status_code, 405)