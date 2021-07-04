from ecommerce.api.models import Product
import factory
import datetime
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from ecommerce.api.models import Product, Order, OrderDetail


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = 'admin'
    password = factory.PostGenerationMethodCall("set_password", "admin")

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: 'Product %s' % n)
    price = 0
    stock = 0

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    date_time = factory.LazyFunction(datetime.datetime.now)

class OrderDetailFactory(DjangoModelFactory):
    class Meta:
        model = OrderDetail
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(Product)
    quantity = 0