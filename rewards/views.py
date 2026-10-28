from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import *
from datetime import date
from django.views.decorators.http import require_POST
import uuid

from .models import *
from .services import *
from .permissions import *

@login_required
def reward_delete(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    if is_petugas(request.user) and request.method == 'POST':
        reward.delete()
    return redirect('rewards:reward_list')

@login_required(login_url='login')
@require_POST
@transaction.atomic
def redeem_reward(request, pk):
    # kunci baris user dan hadiah agar klik ganda tidak memotong poin dua kali
    user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
    reward = get_object_or_404(Reward.objects.select_for_update(), pk=pk)

    if reward.level_minimal > info_poin(user)["level"]:
        messages.error(request, "Level kamu belum cukup untuk hadiah ini.")
    elif reward.stok <= 0:
        messages.error(request, "Stok hadiah habis.")
    elif hitung_poin(user) < reward.harga_poin:
        messages.error(request, "Poin kamu tidak cukup.")
    else:
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
        messages.success(request, f"Berhasil menukar. Kode vouchermu: {redemption.kode}")

    return redirect("rewards:reward_list")


def reward_list(request):
    rewards = Reward.objects.all()

    kategori_aktif = request.GET.get("kategori", "")
    maks_poin = request.GET.get("maks_poin", "")
    if kategori_aktif in dict(Reward.KATEGORI_CHOICES):
        rewards = rewards.filter(kategori=kategori_aktif)
    else:
        kategori_aktif = ""
    if maks_poin.isdigit():
        rewards = rewards.filter(harga_poin__lte=int(maks_poin))

    user = request.user
    if user.is_authenticated:
        info = info_poin(user)
        redemptions = user.redemptions.select_related("reward")[:10]
        transaksi = user.point_transactions.all()[:8]
    else:
        info = {"total_poin": 0, "level": 1,
                "poin_ke_level_berikutnya": 500, "dots": [False] * 10}
        redemptions, transaksi = [], []

    rewards = list(rewards)
    for r in rewards:
        r.terkunci = r.level_minimal > info["level"]

    return render(request, "rewards/reward_list.html", {
        **info,
        "rewards": rewards,
        "redemptions": redemptions,
        "transaksi": transaksi,
        "form": RewardForm() if is_petugas(user) else None,
        "kategori_aktif": kategori_aktif,
        "kategori_list": Reward.KATEGORI_CHOICES,
        "maks_poin": maks_poin,
    })
    
    
def _pesan_error(form):
    hasil = []
    for nama_field, daftar in form.errors.items():
        label = form.fields[nama_field].label if nama_field in form.fields else ''
        for e in daftar:
            hasil.append(f"{label}: {e}" if label else e)
    return " ".join(hasil)



def reward_create(request):
    if request.method == 'POST':
        form = RewardForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hadiah berhasil ditambahkan.')
        else:
            messages.error(request, _pesan_error(form))
    return redirect('rewards:reward_list')


@login_required(login_url='login')
@require_POST
def reward_update(request, pk):
    if not is_petugas(request.user):
        return redirect("rewards:reward_list")

    reward = get_object_or_404(Reward, pk=pk)
    form = RewardForm(request.POST, instance=reward)   # instance wajib
    if form.is_valid():
        form.save()                                    # jangan lupa
        messages.success(request, "Hadiah berhasil diubah.")
    else:
        messages.error(request, _pesan_error(form))
    return redirect("rewards:reward_list")
    
