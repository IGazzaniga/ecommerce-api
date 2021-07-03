from rest_framework import serializers
from ecommerce.api.models import Order, OrderDetail, Product
from django.utils import module_loading
from rest_framework.serializers import ModelSerializer, SerializerMethodField
import requests
from django.db.models import F

class ProductSerializer(ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"

class OrderDetailSerializer(ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = ("product", "quantity",)

class GetOrderSerializer(ModelSerializer):
    total = SerializerMethodField()
    total_usd = SerializerMethodField()
    details = OrderDetailSerializer(many=True)

    class Meta:
        model = Order
        fields =  ("id", "date_time", "details", "total", "total_usd")

    def get_total(self, obj):
        total = 0
        for detail in obj.details.all():
            total += detail.product.price * detail.quantity
        return total

    def get_total_usd(self, obj):
        dollar_data = requests.get("https://www.dolarsi.com/api/api.php?type=valoresprincipales")
        for dollar in dollar_data.json():
            if (dollar.get("casa").get("nombre") == "Dolar Blue"):
                dollar_price = dollar.get("casa").get("venta").replace(",", ".")
        return self.get_total(obj) * float(dollar_price)


class OrderSerializer(ModelSerializer):
    details = OrderDetailSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "date_time", "details",)

    def validate(self, data):
        details = data.get("details")
        products = []
        for detail in details:
            product = detail.get("product")
            if product in products:
                raise serializers.ValidationError(f"Product {product.name} is duplicated")
            products.append(product)
            if product.stock < detail.get("quantity"):
                raise serializers.ValidationError(f"There's not enough stock of {product.name}")

        return data

    def get_total(self, obj):
        total = 0
        for detail in obj.details.all():
            total += detail.product.price * detail.quantity
        return total

    def get_total_usd(self, obj):
        dollar_data = requests.get("https://www.dolarsi.com/api/api.php?type=valoresprincipales")
        for dollar in dollar_data.json():
            if (dollar.get("casa").get("nombre") == "Dolar Blue"):
                dollar_price = dollar.get("casa").get("venta").replace(",", ".")
        return self.get_total(obj) * float(dollar_price)
    
    def create(self, validated_data):
        details = validated_data.get("details")
        order_details = []
        order = Order.objects.create()
        for detail in details:
            product = detail.get("product")
            Product.objects.filter(id=product.id).update(stock=F('stock') - detail.get("quantity"))
            order_detail = OrderDetail(order=order, **detail)
            order_details.append(order_detail)

        OrderDetail.objects.bulk_create(objs=order_details)
        return order

    def update(self, instance, validated_data):
        details = validated_data.get("details")
        instance_details = list(instance.details.all())
        incoming_details = []
    
        for detail in details:
            product = detail.get("product")
            previous_quantity = detail.get("quantity")
            incoming_detail, created = OrderDetail.objects.update_or_create(order=instance, product=product, defaults=detail)
            incoming_details.append(incoming_detail)
            if created:
                stock_difference = detail.get("quantity")
            else:
                previous_quantity = instance_details[instance_details.index(incoming_detail)].quantity
                stock_difference = incoming_detail.quantity - previous_quantity

            Product.objects.filter(id=product.id).update(stock=F('stock') - stock_difference)

        deleted_details = set(instance_details) - set(incoming_details)
        for deleted in deleted_details:
            detail = OrderDetail.objects.get(id=deleted.id)
            Product.objects.filter(id=detail.product.id).update(stock=F('stock') + detail.quantity)
            detail.delete()

        instance.details.set(incoming_details, clear=True)
        return instance
