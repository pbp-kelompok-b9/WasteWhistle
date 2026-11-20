from rest_framework import serializers

from .models import Reward, Redemption, PointTransaction


class RewardSerializer(serializers.ModelSerializer):
    kategori_label = serializers.CharField(
        source="get_kategori_display", read_only=True
    )
    terkunci = serializers.SerializerMethodField()

    class Meta:
        model = Reward
        fields = [
            "id",
            "nama",
            "deskripsi",
            "kategori",
            "kategori_label",
            "harga_poin",
            "stok",
            "gambar",
            "level_minimal",
            "terkunci",
        ]

    def get_terkunci(self, obj):
        # level pengguna dihitung sekali di ViewSet lalu dikirim lewat context
        return obj.level_minimal > self.context.get("level", 1)


class RedemptionSerializer(serializers.ModelSerializer):
    nama = serializers.CharField(source="reward.nama", read_only=True)
    gambar = serializers.CharField(source="reward.gambar", read_only=True)

    class Meta:
        model = Redemption
        fields = ["id", "nama", "gambar", "tanggal", "kode", "poin_dipakai"]


class PointTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointTransaction
        fields = ["id", "alasan", "jumlah", "tanggal"]