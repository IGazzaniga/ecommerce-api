# E-commerce API

## Development
After cloning the project, create a new environment by running

`pipenv shell`

and install dependencies with

`pipenv install`

For running tests, run

`python manage.py test`

## Endpoints

For every operation, authentication using JWT is required.
### Products
- List all products `GET /api/products`
- Get specific product `GET /api/products/{id}`
- Update product `PUT /api/products/{id}/`
- Create product `POST /api/products/`
- Update product stock `PUT /api/products/{id}/update_stock/`
- Delete product `DELETE /api/products/{id}/`


### Orders
- List all orders `GET /api/orders`
- Get specific order `GET /api/orders/{id}`
- Update order `PUT /api/orders/{id}/`
- Create order `POST /api/orders/`
