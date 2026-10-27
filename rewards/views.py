from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Reward
from .forms import RewardForm
from datetime import date

def is_petugas(user):
    return user.is_staff

# @login_required
def reward_delete(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    # if is_petugas(request.user) and 
    if request.method == 'POST':
        reward.delete()
    return redirect('rewards:reward_list')

@login_required
@transaction.atomic
def redeem_reward(request, pk):
    if request.method != 'POST':
        return redirect('rewards:reward_list')

    reward = get_object_or_404(Reward.objects.select_for_update(), pk=pk)
    poin_user = 1000  # fungsi 

    if reward.stok <= 0:
        messages.error(request, 'Stok habis.')
    elif poin_user < reward.harga_poin:
        messages.error(request, 'Poin tidak cukup.')
    else:
        reward.stok -= 1
        reward.save()
        # catat Redemption dan PointTransaction
        messages.success(request, 'Penukaran berhasil.')
    return redirect('rewards:reward_list')


def reward_list(request):
    total_poin = 1420
    level = 3
    poin_ke_level_berikutnya = 80

    rewards = Reward.objects.all()
    
    kategori_aktif = request.GET.get("kategori", "")
    maks_poin = request.GET.get("maks_poin", "")
    
    if kategori_aktif in dict(Reward.KATEGORI_CHOICES):
        rewards = rewards.filter(kategori=kategori_aktif)
    else:
        kategori_aktif = ""
        
    if maks_poin.isdigit():
        rewards = rewards.filter(harga_poin__lte=int(maks_poin))
    
    redemptions = [
        {"reward": {"nama": "Transit credit Rp 25,000"}, "tanggal": date(2026, 10, 20), "status": "selesai", "kode": "WW-4821"},
        {"reward": {"nama": "15% off at the refill store"}, "tanggal": date(2026, 10, 23), "status": "diproses", "kode": ""},
    ]

    return render(request, 'rewards/reward_list.html', {
        'total_poin': total_poin,
        'level': level,
        'poin_ke_level_berikutnya': poin_ke_level_berikutnya,
        'dots': [True] * 9 + [False],   # 9 bulatan penuh, 1 putus-putus
        'rewards': rewards,
        'redemptions': redemptions,
        'form': RewardForm,
        'kategori_aktif': kategori_aktif,
        'kategori_list': Reward.KATEGORI_CHOICES,
        'maks_poin': maks_poin,
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


# @login_required
def reward_update(request, pk):
    # if not request.user.is_staff:
    #     return redirect('rewards:reward_list')
    reward = get_object_or_404(Reward, pk=pk)
    if request.method == 'POST':
        form = RewardForm(request.POST, instance=reward)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hadiah berhasil diubah.')
        else:
            messages.error(request, _pesan_error(form))
    return redirect('rewards:reward_list')
    
