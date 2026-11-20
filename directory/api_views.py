from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from directory.models import WasteBank
from directory.permissions import IsPortfolioOwnerOrStaffOrReadOnly, IsPortfolioOwnerOrReadOnly
from directory.serializers import WasteBankSerializer


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrReadOnly])
def wastebank_list(request):
    if request.method in ("GET", "HEAD"):
        wastebanks = WasteBank.objects.order_by("name", "id")
        name_query = request.query_params.get("name", "").strip()
        if name_query:
            wastebanks = wastebanks.filter(
                Q(name__icontains=name_query)
                | Q(address__icontains=name_query)
                | Q(contact_number__icontains=name_query)
                | Q(email__icontains=name_query)
            )
        serializer = WasteBankSerializer(
            wastebanks, many=True, context={"request": request},
        )
        return Response(serializer.data)

    serializer = WasteBankSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrStaffOrReadOnly])
def wastebank_detail(request, wastebank_id):
    wastebank = get_object_or_404(
        WasteBank.objects, pk=wastebank_id,
    )
    if request.method in ("GET", "HEAD"):
        serializer = WasteBankSerializer(wastebank, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        wastebank.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = WasteBankSerializer(
        wastebank, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)