from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Reward

def is_petugas(user):
    # sesuaikan dengan cara tim membedakan peran
    return user.is_staff

@login_required
def reward_create(request):
    if not is_petugas(request.user):
        return redirect('reward_list')
    if request.method == 'POST':
        Reward.objects.create(
            nama=request.POST['nama'],
            deskripsi=request.POST.get('deskripsi', ''),
            harga_poin=request.POST['harga_poin'],
            stok=request.POST['stok'],
        )
        messages.success(request, 'Hadiah ditambahkan.')
        return redirect('reward_list')
    return render(request, 'rewards/reward_form.html')

@login_required
def reward_update(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    if not is_petugas(request.user):
        return redirect('reward_list')
    if request.method == 'POST':
        reward.nama = request.POST['nama']
        reward.harga_poin = request.POST['harga_poin']
        reward.stok = request.POST['stok']
        reward.save()
        return redirect('reward_list')
    return render(request, 'rewards/reward_form.html', {'reward': reward})

@login_required
def reward_delete(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    if is_petugas(request.user) and request.method == 'POST':
        reward.delete()
    return redirect('reward_list')

@login_required
@transaction.atomic
def redeem_reward(request, pk):
    if request.method != 'POST':
        return redirect('reward_list')

    reward = get_object_or_404(Reward.objects.select_for_update(), pk=pk)
    poin_user = 1000  # fungsi buatanmu

    if reward.stok <= 0:
        messages.error(request, 'Stok habis.')
    elif poin_user < reward.harga_poin:
        messages.error(request, 'Poin tidak cukup.')
    else:
        reward.stok -= 1
        reward.save()
        # catat Redemption dan PointTransaction (poin keluar) di sini
        messages.success(request, 'Penukaran berhasil.')
    return redirect('reward_list')


def reward_list(request):
    total_poin = 1420
    level = 3
    poin_ke_level_berikutnya = 80

    rewards = [
        {"pk": 1, "nama": "Transit credit Rp 25,000", "harga_poin": 250, "terkunci": False},
        {"pk": 2, "nama": "15% off at the refill store", "harga_poin": 180, "terkunci": False},
        {"pk": 3, "nama": "Plant one tree in your ward", "harga_poin": 500, "terkunci": False},
        {"pk": 4, "nama": "Summit invite with city officials", "harga_poin": 1000,
         "terkunci": True, "level_minimal": 4},
        {"pk": 5, "nama": "TESTINGTESTINGTESTING", "harga_poin": 100, "terkunci": False},
    ]

    return render(request, 'rewards/reward_list.html', {
        'total_poin': total_poin,
        'level': level,
        'poin_ke_level_berikutnya': poin_ke_level_berikutnya,
        'dots': [True] * 9 + [False],   # 9 bulatan penuh, 1 putus-putus
        'rewards': rewards,
    })
