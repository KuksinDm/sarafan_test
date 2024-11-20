import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from products.models import Cart, Category, Product, Subcategory

User = get_user_model()


@pytest.fixture
def user(db):
    """Создание и возврат пользователя для тестирования."""
    return User.objects.create_user(username='testuser', password='password')


@pytest.fixture
def auth_token(user):
    """Создание и возврат токена для пользователя"""
    token, created = Token.objects.get_or_create(user=user)
    return token.key


@pytest.fixture
def category(db):
    """Фикстура для создания категории."""
    return Category.objects.create(
        name="Test Category",
        slug="test-category",
        image="categories/category_default.jpg"
    )


@pytest.fixture
def subcategory(db, category):
    """Фикстура для создания подкатегории."""
    return Subcategory.objects.create(
        name="Test Subcategory",
        slug="test-subcategory",
        category=category,
        image="subcategories/subcategory_default.jpg"
    )


@pytest.fixture
def product(db, category, subcategory):
    """Фикстура для создания продукта."""
    return Product.objects.create(
        name="Test Product",
        slug="test-product",
        category=category,
        subcategory=subcategory,
        price=100.0,
        image="products/default.jpg"
    )


@pytest.fixture
def cart(db, user):
    """Фикстура для создания корзины."""
    return Cart.objects.create(user=user)
