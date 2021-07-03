from django.db import models
from django.core.validators import MinValueValidator
# Create your models here.

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    stock = models.IntegerField(validators=[MinValueValidator(limit_value=0)])

class Order(models.Model):
    date_time = models.DateTimeField(auto_now=True)
    products = models.ManyToManyField(Product, through='OrderDetail')

class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="details", null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_details")
    quantity = models.IntegerField()

