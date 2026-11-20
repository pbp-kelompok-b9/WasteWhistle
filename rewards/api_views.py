import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import ProtectedError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Reward, Redemption, PointTransaction
from .permissions import is_petugas
from .serializers import (
    RewardSerializer,
    RedemptionSerializer,
    PointTransactionSerializer,
)
from .services import info_poin, hitung_poin


class IsPetugasOrReadOnly(permissions.BasePermission):
    """GET terbuka untuk semua; POST/PUT/PATCH/DELETE hanya untuk petugas."""

    message = "Hanya petugas yang dapat mengelola hadiah."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and is_petugas(request.user))


class RewardViewSet(viewsets.ModelViewSet):
    """
    GET    /api/v1/rewards/                 daftar hadiah (?kategori=&maks_poin=&tersedia=1)
    POST   /api/v1/rewards/                 buat hadiah          (petugas)
    GET    /api/v1/rewards/{id}/            detail hadiah
    PUT    /api/v1/rewards/{id}/            ubah hadiah          (petugas)
    PATCH  /api/v1/rewards/{id}/            ubah sebagian        (petugas)
    DELETE /api/v1/rewards/{id}/            hapus hadiah         (petugas)
    POST   /api/v1/rewards/{id}/redeem/     tukar poin dengan hadiah (login)
    GET    /api/v1/rewards/me/              poin, level, voucher, riwayat milik user
    """

    serializer_class = RewardSerializer
    permission_classes = [IsPetugasOrReadOnly]

    def get_queryset(self):
        qs = Reward.objects.all()
        if self.action != "list":
            return qs

        params = self.request.query_params
        kategori = params.get("kategori", "").strip()
        maks_poin = params.get("maks_poin", "").strip()
        tersedia = params.get("tersedia", "").strip()

        if kategori in dict(Reward.KATEGORI_CHOICES):
            qs = qs.filter(kategori=kategori)
        if maks_poin.isdigit():
            qs = qs.filter(harga_poin__lte=int(maks_poin))
        if tersedia == "1":
            qs = qs.filter(stok__gt=0)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        context["level"] = info_poin(user)["level"] if user.is_authenticated else 1
        return context

    def destroy(self, request, *args, **kwargs):
        reward = self.get_object()
        nama = reward.nama
        try:
            reward.delete()
        except ProtectedError:
            return Response(
                {
                    "message": (
                        "Hadiah ini sudah pernah ditukar, jadi tidak bisa dihapus. "
                        "Ubah stoknya menjadi 0 jika ingin menandainya habis."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response({"message": f'Hadiah "{nama}" dihapus.'}, status=status.HTTP_200_OK)

    # ---------- aksi khusus ----------

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def redeem(self, request, pk=None):
        with transaction.atomic():
            # kunci baris user dan hadiah agar klik ganda tidak memotong poin dua kali
            user = get_user_model().objects.select_for_update().get(pk=request.user.pk)
            reward = Reward.objects.select_for_update().filter(pk=pk).first()
            if reward is None:
                return Response(
                    {"message": "Hadiah tidak ditemukan."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if reward.level_minimal > info_poin(user)["level"]:
                return Response(
                    {"message": "Level kamu belum cukup untuk hadiah ini."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if reward.stok <= 0:
                return Response(
                    {"message": "Stok hadiah habis."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if hitung_poin(user) < reward.harga_poin:
                return Response(
                    {"message": "Poin kamu tidak cukup."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

        return Response(
            {
                "message": f"Berhasil menukar. Kode vouchermu: {redemption.kode}",
                "kode": redemption.kode,
            },
            status=status.HTTP_201_CREATED,
        )

    @method_decorator(never_cache)
    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[permissions.AllowAny],
    )
    def me(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response(
                {
                    "authenticated": False,
                    "total_poin": 0,
                    "level": 1,
                    "poin_ke_level_berikutnya": 500,
                    "dots": [False] * 10,
                    "redemptions": [],
                    "transaksi": [],
                }
            )

        redemptions = user.redemptions.select_related("reward")[:10]
        transaksi = user.point_transactions.all()[:8]
        return Response(
            {
                **info_poin(user),
                "authenticated": True,
                "redemptions": RedemptionSerializer(redemptions, many=True).data,
                "transaksi": PointTransactionSerializer(transaksi, many=True).data,
            }
        )