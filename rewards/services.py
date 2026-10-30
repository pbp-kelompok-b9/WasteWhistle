from django.db.models import Sum
from .models import PointTransaction

POIN_PER_LEVEL = 500


def hitung_poin(user):
    return PointTransaction.objects.filter(user=user).aggregate(
        total=Sum("jumlah"))["total"] or 0


def tambah_poin(user, jumlah, alasan, referensi=""):
    if referensi and PointTransaction.objects.filter(
            user=user, referensi=referensi).exists():
        return None
    return PointTransaction.objects.create(
        user=user, jumlah=jumlah, alasan=alasan, referensi=referensi)


def info_poin(user):
    saldo = hitung_poin(user)
    # level dihitung dari total poin yang PERNAH didapat, jadi menukar hadiah tidak menurunkan level
    diperoleh = PointTransaction.objects.filter(
        user=user, jumlah__gt=0).aggregate(t=Sum("jumlah"))["t"] or 0
    level = diperoleh // POIN_PER_LEVEL + 1
    terisi = (diperoleh % POIN_PER_LEVEL) * 10 // POIN_PER_LEVEL
    return {
        "total_poin": saldo,
        "level": level,
        "poin_ke_level_berikutnya": level * POIN_PER_LEVEL - diperoleh,
        "dots": [True] * terisi + [False] * (10 - terisi),
    }