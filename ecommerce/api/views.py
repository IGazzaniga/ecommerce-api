from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Order, OrderDetail, Product
from rest_framework.decorators import action
from .serializers import ProductSerializer, OrderSerializer, OrderDetailSerializer,GetOrderSerializer
from rest_framework.response import Response
from django.db.models import F


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["POST"])
    def update_stock(self, request, pk):
        product = self.get_object()
        stock = request.data.get("stock")

        if int(stock) >= 0:
            product.stock = stock
            product.save()
            return Response(status=status.HTTP_200_OK)
        return Response({"Error": "Stock must be equal or greater than 0"}, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in("list", "retrieve"):
            return GetOrderSerializer
        return OrderSerializer

    def destroy(self, request, pk):
        order = self.get_object()
        for detail in order.details.all():
            quantity = detail.quantity
            Product.objects.filter(id=detail.product.id).update(stock=F('stock') + quantity)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

