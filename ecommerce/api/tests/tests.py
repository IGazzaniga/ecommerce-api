from django.test import TestCase, client

# Create your tests here.
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .factory import OrderDetailFactory, OrderFactory, ProductFactory, UserFactory
from ecommerce.api.models import Product, Order, OrderDetail
import json

def login(client, admin):
    token_request = client.post("/api/token/", {'username': admin.username, 'password': 'admin'})
    token = token_request.data.get("access")
    client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token))

class EcommerceApiTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.admin = UserFactory.create()
        product_1 = ProductFactory.create(price=3.00, stock=30)
        product_2 = ProductFactory.create(price=5.00, stock=5)
        product_3 = ProductFactory.create(price=1.00, stock=10)
        order = OrderFactory.create()
        OrderDetailFactory.create(order=order, product=product_1, quantity=15)

    def test_non_authenticated_request(self):
        request = self.client.get("/api/products/")
        self.assertEqual(request.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_request(self):
        login(self.client, self.admin)
        request = self.client.get("/api/products/")
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_get_all_products(self):
        login(self.client, self.admin)
        request = self.client.get("/api/products/")
        self.assertEqual(request.data.get("count"), 3)

    def test_get_specific_product(self):
        login(self.client, self.admin)
        request = self.client.get("/api/products/1/")
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_delete_product(self):
        login(self.client, self.admin)
        new_name = 'edited product'
        request = self.client.delete("/api/products/1/")
        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 2)

    def test_create_new_product(self):
        login(self.client, self.admin)
        request = self.client.post("/api/products/", {'name': 'new product', 'stock': 17, 'price': 7.50})
        self.assertEqual(request.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 4)
    
    def test_edit_new_product(self):
        login(self.client, self.admin)
        new_name = 'edited product'
        request = self.client.put("/api/products/1/", {'name': new_name, 'stock': 1, 'price': 15.50})
        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.assertEqual(Product.objects.get(pk=1).name, new_name)

    def test_edit_product_stock(self):
        login(self.client, self.admin)
        new_stock = 100
        request = self.client.post("/api/products/1/update_stock/", {'stock': new_stock})
        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.assertEqual(Product.objects.get(pk=1).stock, new_stock)

    def test_edit_product_negative_stock(self):
        login(self.client, self.admin)
        new_stock = -100
        request = self.client.post("/api/products/1/update_stock/", {'stock': new_stock})
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_all_orders(self):
        login(self.client, self.admin)
        request = self.client.get("/api/orders/")
        self.assertEqual(request.data.get("count"), 1)
    
    def test_get_specific_order(self):
        login(self.client, self.admin)
        request = self.client.get("/api/orders/1/")
        self.assertEqual(len(request.data.get("details")), 1)
        self.assertEqual(request.data.get("total"), 45.00)

    def test_create_new_order(self):
        login(self.client, self.admin)
        data= {
            "details":
            [
                {
                    "product": 1,
                    "quantity": 2
                },
                {
                    "product": 3,
                    "quantity": 1
                }
            ]
        }
        product_1_previous_stock = Product.objects.get(pk=1).stock
        product_3_previous_stock = Product.objects.get(pk=3).stock
    
        request = self.client.post('/api/orders/', data=data, format="json")

        self.assertEqual(request.status_code, status.HTTP_201_CREATED)
        self.assertEqual(product_1_previous_stock, Product.objects.get(pk=1).stock + 2)
        self.assertEqual(product_3_previous_stock, Product.objects.get(pk=3).stock + 1)


    def test_create_order_duplicated_product(self):
        login(self.client, self.admin)
        data= {
            "details":
            [
                {
                    "product": 3,
                    "quantity": 1
                },
                {
                    "product": 3,
                    "quantity": 2
                }
            ]
        }
        request = self.client.post("/api/orders/", data=data, format="json")
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        message_error = json.loads(request.content).get("non_field_errors")[0]
        self.assertIn("is duplicated", message_error)


    def test_create_order_not_enough_stock_of_product(self):
        login(self.client, self.admin)
        data= {
            "details":
            [
                {
                    "product": 3,
                    "quantity": 1000,
                },
            ]
        }
        request = self.client.post("/api/orders/", data=data, format="json")
        self.assertEqual(request.status_code, status.HTTP_400_BAD_REQUEST)
        message_error = json.loads(request.content).get("non_field_errors")[0]
        self.assertIn("There's not enough stock", message_error)

    def test_delete_order_and_restore_stock(self):
        login(self.client, self.admin)
        order_detail = Order.objects.get(pk=1).details.first()
        product_to_restore = order_detail.product.id
        product_previous_stock = order_detail.product.stock
        stock_to_restore = order_detail.quantity
        request = self.client.delete("/api/orders/1/")
        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.get(id=product_to_restore).stock, product_previous_stock+stock_to_restore)

    def test_update_order_and_product_stock(self):
        login(self.client, self.admin)
        order_detail = Order.objects.get(pk=1).details.first()
        product_to_restore = order_detail.product.id
        product_1_previous_quantity = order_detail.quantity

        product_1_previous_stock = Product.objects.get(pk=1).stock
        product_2_previous_stock = Product.objects.get(pk=2).stock
        
        new_quantity = 10
        data= {
            "details":
            [
                {
                    "product": 1,
                    "quantity": new_quantity,
                },
                {
                    "product": 2,
                    "quantity": 2,
                },
            ]
        }
        stock_difference = new_quantity - product_1_previous_quantity
        request = self.client.put("/api/orders/1/", data=data, format="json")

        self.assertEqual(request.status_code, status.HTTP_200_OK)
        self.assertEqual(Product.objects.get(id=product_to_restore).stock, product_1_previous_stock-stock_difference)

        self.assertEqual(Product.objects.get(id=2).stock, product_2_previous_stock-2)
        self.assertEqual(OrderDetail.objects.count(), 2)