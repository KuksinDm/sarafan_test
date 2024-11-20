import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from products.models import CartItem


@pytest.mark.parametrize(
    'name, kwargs, expected_status',
    [
        ('api:category-list', {}, status.HTTP_200_OK),
        ('api:category-detail', {'pk': None}, status.HTTP_200_OK),
        ('api:product-list', {}, status.HTTP_200_OK),
        ('api:product-detail', {'pk': None}, status.HTTP_200_OK),
    ]
)
@pytest.mark.django_db
def test_pages_availability_for_users(
    client,
    name,
    kwargs,
    expected_status,
    category,
    product,
    auth_token
):
    """
    Тестирует доступность различных API-страниц для пользователей как без
    авторизации, так и с авторизацией через токен.
    Проверяет, что страницы возвращают правильный HTTP статус.
    """
    if 'pk' in kwargs:
        if name == 'api:category-detail':
            kwargs['pk'] = category.pk
        elif name == 'api:product-detail':
            kwargs['pk'] = product.pk

    url = reverse(name, kwargs=kwargs)

    response = client.get(url)
    assert response.status_code == expected_status

    response = client.get(url, HTTP_AUTHORIZATION='Token ' + auth_token)
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_cart_list_access(client, user, auth_token):
    """
    Тестирует доступ к списку корзины. Проверяет, что неавторизованный
    пользователь получает статус 401, а авторизованный — статус 200.
    """
    url = reverse('api:cart-list')

    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get(url, HTTP_AUTHORIZATION='Token ' + auth_token)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_add_product_to_cart(user, auth_token, product, cart):
    """
    Тестирует добавление товара в корзину. Проверяет, что неавторизованные
    пользователи не могут добавлять товары, в то время как авторизованные могут
    добавлять товары в корзину.
    Также проверяется, что количество товаров в корзине обновляется корректно
    при добавлении одного и того же товара несколько раз.
    """

    client = APIClient()

    url = reverse('api:cart-add')
    data = {
        'product_id': product.id,
        'quantity': 1
    }

    response = client.post(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    client.credentials(HTTP_AUTHORIZATION='Token ' + auth_token)

    response = client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['success'] == 'Product added to cart.'

    cart_item = CartItem.objects.get(cart=cart, product=product)
    assert cart_item.quantity == 1

    data['quantity'] = 2
    response = client.post(url, data)
    assert response.status_code == status.HTTP_201_CREATED
    cart_item.refresh_from_db()
    assert cart_item.quantity == 3
