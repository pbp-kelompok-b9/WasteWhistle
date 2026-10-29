from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError
from .forms import *
from datetime import date
from django.views.decorators.http import require_POST, require_GET
import uuid
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.decorators.cache import never_cache

from .models import *
from .services import *
from .permissions import *


# Helper
 
def _tanggal(dt, pola):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return date_format(dt, pola)
 
 
def _tolak_bila_bukan_petugas(request):
    """Mengembalikan JsonResponse kalau pengguna bukan petugas, selain itu None."""
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Silakan login terlebih dahulu."}, status=401)
    if not is_petugas(request.user):
        return JsonResponse(
            {"message": "Hanya petugas yang dapat mengelola hadiah."}, status=403
        )
    return None
 
 
# Halaman
 
def reward_list(request):
    kategori_aktif = request.GET.get("kategori", "")
    if kategori_aktif not in dict(Reward.KATEGORI_CHOICES) and kategori_aktif != "tersedia":
        kategori_aktif = ""
 
    maks_poin = request.GET.get("maks_poin", "")
    if not maks_poin.isdigit():
        maks_poin = ""
 
    petugas = is_petugas(request.user)
    return render(request, "rewards/reward_list.html", {
        "active_page": "reward",
        "is_petugas": petugas,
        "form": RewardForm() if petugas else None,
        "kategori_list": Reward.KATEGORI_CHOICES,
        "kategori_aktif": kategori_aktif,
        "maks_poin": maks_poin,
    })
 
 
# Endpoint JSON get
 
@require_GET
def get_rewards_json(request):
    """Katalog hadiah, bisa difilter ?kategori=...&maks_poin=..."""
    rewards = Reward.objects.all()
 
    kategori = request.GET.get("kategori", "").strip()
    maks_poin = request.GET.get("maks_poin", "").strip()

    if kategori in dict(Reward.KATEGORI_CHOICES):
        rewards = rewards.filter(kategori=kategori)
        
    if maks_poin.isdigit():
        rewards = rewards.filter(harga_poin__lte=int(maks_poin))
 
    level = info_poin(request.user)["level"] if request.user.is_authenticated else 1
 
    data = []
    for r in rewards:
        data.append({
            "pk": str(r.pk),
            "fields": {
                "nama": r.nama,
                "deskripsi": r.deskripsi,
                "kategori": r.kategori,
                "kategori_label": r.get_kategori_display(),
                "harga_poin": r.harga_poin,
                "stok": r.stok,
                "gambar": r.gambar,
                "level_minimal": r.level_minimal,
                "terkunci": r.level_minimal > level,
            },
        })
    return JsonResponse(data, safe=False)
 
 
@require_GET
@never_cache
def get_my_rewards_json(request):
    """Poin, level, voucher, dan riwayat poin milik pengguna yang sedang login."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({
            "authenticated": False,
            "total_poin": 0,
            "level": 1,
            "poin_ke_level_berikutnya": 500,
            "dots": [False] * 10,
            "redemptions": [],
            "transaksi": [],
        })
 
    redemptions = [
        {
            "pk": str(r.pk),
            "nama": r.reward.nama,
            "gambar": r.reward.gambar,
            "tanggal": _tanggal(r.tanggal, "d M Y"),
            "kode": r.kode,
            "poin_dipakai": r.poin_dipakai,
        }
        for r in user.redemptions.select_related("reward")[:10]
    ]
    transaksi = [
        {
            "pk": str(t.pk),
            "alasan": t.alasan,
            "jumlah": t.jumlah,
            "tanggal": _tanggal(t.tanggal, "d M Y, H:i"),
        }
        for t in user.point_transactions.all()[:8]
    ]
 
    return JsonResponse({
        **info_poin(user),
        "authenticated": True,
        "redemptions": redemptions,
        "transaksi": transaksi,
    })
 
 
# Endpoint AJAX postS
 
@require_POST
def create_reward_ajax(request):
    gagal = _tolak_bila_bukan_petugas(request)
    if gagal:
        return gagal
 
    form = RewardForm(request.POST)
    if form.is_valid():
        reward = form.save()
        return JsonResponse(
            {"message": "Hadiah berhasil ditambahkan.", "pk": str(reward.pk)},
            status=201,
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
 
 
@require_POST
def update_reward_ajax(request, pk):
    gagal = _tolak_bila_bukan_petugas(request)
    if gagal:
        return gagal
 
    reward = Reward.objects.filter(pk=pk).first()
    if reward is None:
        return JsonResponse({"message": "Hadiah tidak ditemukan."}, status=404)
 
    form = RewardForm(request.POST, instance=reward)
    if form.is_valid():
        form.save()
        return JsonResponse({"message": "Hadiah berhasil diubah.", "pk": str(reward.pk)})
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
 
 
@require_POST
def delete_reward_ajax(request, pk):
    gagal = _tolak_bila_bukan_petugas(request)
    if gagal:
        return gagal
 
    reward = Reward.objects.filter(pk=pk).first()
    if reward is None:
        return JsonResponse({"message": "Hadiah tidak ditemukan."}, status=404)
 
    nama = reward.nama
    try:
        reward.delete()
    except ProtectedError:
        return JsonResponse(
            {
                "message": (
                    "Hadiah ini sudah pernah ditukar, jadi tidak bisa dihapus. "
                    "Ubah stoknya menjadi 0 jika ingin menandainya habis."
                )
            },
            status=409,
        )
    return JsonResponse({"message": f'Hadiah "{nama}" dihapus.'})
 
 
# Endpoint AJAX redeem
 
@require_POST
@transaction.atomic
def redeem_reward_ajax(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Silakan login untuk menukar poin."}, status=401)
 
    # kunci baris user dan hadiah agar klik ganda tidak memotong poin dua kali
    user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
    reward = Reward.objects.select_for_update().filter(pk=pk).first()
    if reward is None:
        return JsonResponse({"message": "Hadiah tidak ditemukan."}, status=404)
 
    if reward.level_minimal > info_poin(user)["level"]:
        return JsonResponse(
            {"message": "Level kamu belum cukup untuk hadiah ini."}, status=400
        )
    if reward.stok <= 0:
        return JsonResponse({"message": "Stok hadiah habis."}, status=400)
    if hitung_poin(user) < reward.harga_poin:
        return JsonResponse({"message": "Poin kamu tidak cukup."}, status=400)
 
    reward.stok -= 1
    reward.save(update_fields=["stok"])
 
    redemption = Redemption.objects.create(
        user=user,
        reward=reward,
        poin_dipakai=reward.harga_poin,
        kode=f"WW-{uuid.uuid4().hex[:6].upper()}",
    )
    PointTransaction.objects.create(
        user=user,
        jumlah=-reward.harga_poin,
        alasan=f"Tukar: {reward.nama}",
        referensi=f"redeem-{redemption.pk}",
    )
    return JsonResponse(
        {
            "message": f"Berhasil menukar. Kode vouchermu: {redemption.kode}",
            "kode": redemption.kode,
        },
        status=201,
    )
 