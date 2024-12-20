from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers

from backend.constants import MIN_QUANTITY
from products.models import Cart, CartItem, Category, Product, Subcategory


User = get_user_model()


class SubcategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с подкатегориями продуктов.

    Поля:
        - id: Идентификатор подкатегории.
        - name: Название подкатегории.
        - slug: Слаг для подкатегории.
        - image: Изображение подкатегории.
    """
    image = serializers.ImageField()

    class Meta:
        model = Subcategory
        fields = ('id', 'name', 'slug', 'image')


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с категориями продуктов.

    Поля:
        - id: Идентификатор категории.
        - name: Название категории.
        - slug: Слаг для категории.
        - image: Изображение категории.
        - subcategories: Список подкатегорий этой категории.
    """
    image = serializers.ImageField()
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'subcategories')


class CategoryProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения категории продукта без входящих в нее
    подкатегорий.

    Поля:
        - id: Идентификатор категории.
        - name: Название категории.
        - slug: Слаг категории.
        - image: Изображение категории.
    """
    image = serializers.ImageField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image')


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для работы с продуктами.

    Поля:
        - id: Идентификатор продукта.
        - name: Название продукта.
        - slug: Слаг продукта.
        - image_small: Маленькое изображение продукта.
        - image_medium: Среднее изображение продукта.
        - image_large: Большое изображение продукта.
        - category: Информация о категории продукта.
        - subcategory: Информация о подкатегории продукта.
        - price: Цена продукта.
    """
    image_small = serializers.ImageField(read_only=True)
    image_medium = serializers.ImageField(read_only=True)
    image_large = serializers.ImageField(read_only=True)
    category = CategoryProductSerializer(read_only=True)
    subcategory = SubcategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'image_small', 'image_medium',
                  'image_large', 'category', 'subcategory', 'price')


class CartItemWithDetailsSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения продуктов в корзине с полной информацией
    о продукте (включая вложенные данные).
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        required=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity']


class CartItemAddSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления или обновления товара в корзине без вложенной
    информации о продукте.
    """
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        required=True
    )
    quantity = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10_000_000)],
        required=True
    )

    class Meta:
        model = CartItem
        fields = ['product_id', 'quantity']

    def validate(self, data):
        # Пример дополнительной валидации, если нужно
        if data['quantity'] < MIN_QUANTITY:
            raise serializers.ValidationError(
                {'quantity': f'Quantity must be at least {MIN_QUANTITY}.'}
            )
        return data


class CartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения корзины пользователя.

    Поля:
        - id: Идентификатор корзины.
        - user: Пользователь, которому принадлежит корзина.
        - items: Список товаров в корзине.
        - total_quantity: Общее количество товаров в корзине.
        - total_price: Общая стоимость товаров в корзине.
    """
    items = CartItemWithDetailsSerializer(many=True, read_only=True)
    total_quantity = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_quantity', 'total_price']

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        return sum(
            item.quantity * item.product.price for item in obj.items.all()
        )
