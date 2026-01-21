from locust import HttpUser, task, between

from random import randint


class DjangoAuthorizedUser(HttpUser):
    weight = 2
    wait_time = between(1, 3)
    csrf_token = None

    def on_start(self):
        response = self.client.get('/accounts/login/')
        self.csrf_token = response.cookies.get('csrftoken')

        self.client.post('/accounts/login/',
            data={
                'email': 'locust_user@gmail.com',
                'password': 'dfhr88vbdsSD',
            },
            headers={'X-CSRFToken': self.csrf_token}
        )

    def on_stop(self):
        print(f'Logging out user (csrf: {self.csrf_token})')
        self.client.post('/core/cart-clear-out/', headers={'X-CSRFToken': self.csrf_token})
        response = self.client.post('/accounts/logout/', headers={'X-CSRFToken': self.csrf_token})
        print(f'Logout status: {response.status_code}')

    @task
    def product_list(self):
        self.client.get('/core/products/')

    @task
    def cart(self):
        self.client.get('/core/order-items/')

    @task(3)
    def add_to_cart(self):
        pk = randint(1, 5)
        self.client.post(f'/core/order-items/{pk}/create/',
            headers={'X-CSRFToken': self.csrf_token}
        )

    @task(2)
    def remove_form_cart(self):
        pk = randint(1, 5)
        self.client.post(f'/core/order-items/{pk}/delete/',
            headers={'X-CSRFToken': self.csrf_token}
        )


class DjangoAnonymousUser(HttpUser):
    weight = 3
    wait_time = between(1, 3)
    csrf_token = None

    def on_start(self):
        response = self.client.get('/accounts/login/')
        self.csrf_token = response.cookies.get('csrftoken')

    def on_stop(self):
        print(f'Clearing cart by anonymous user (csrf: {self.csrf_token})')
        response = self.client.post('/core/cart-clear-out/', headers={'X-CSRFToken': self.csrf_token})
        print(f'Clearing cart status: {response.status_code}')

    @task
    def product_list(self):
        self.client.get('/core/products/')

    @task
    def cart(self):
        self.client.get('/core/order-items/')

    @task(3)
    def add_to_cart(self):
        pk = randint(1, 5)
        self.client.post(f'/core/order-items/{pk}/create/', headers={'X-CSRFToken': self.csrf_token})

    @task(2)
    def remove_from_cart(self):
        pk = randint(1, 5)
        self.client.post(f'/core/order-items/{pk}/delete/', headers={'X-CSRFToken': self.csrf_token})