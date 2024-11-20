from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from .serializers import (
    CartItemSerializer,
    CartSerializer,
    CategorySerializer,
    ProductSerializer,
)
from products.models import Cart, CartItem, Category, Product

User = get_user_model()


class CategoryViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для работы с категориями продуктов.

    Доступ:
        - GET: Получение списка категорий или детализированной информации
        по категории.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(ReadOnlyModelViewSet):
    """
    ViewSet для работы с продуктами.

    Доступ:
        - GET: Получение списка продуктов или детализированной информации
        по продукту.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]


class CartViewSet(ViewSet):
    """
    ViewSet для управления корзиной пользователя.

    Доступ:
        - GET: Получение информации о корзине пользователя.
        - POST: Добавление продукта в корзину.
        - PUT: Обновление количества товара в корзине.
        - DELETE: Удаление товара из корзины или очистка корзины.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.prefetch_related(
            'items__product').get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(
            {'success': 'Product added to cart.'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['put'])
    def update_quantity(self, request):
        """Обновить количество продукта в корзине."""
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        cart_item = get_object_or_404(
            CartItem, cart=request.user.shopping_cart, product=product
        )

        cart_item.quantity = quantity
        cart_item.save()

        return Response(
            {'success': 'Product quantity updated.'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        product_id = request.data.get('product_id')

        if not product_id:
            return Response(
                {'error': 'Product ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item = get_object_or_404(
            CartItem, cart=request.user.shopping_cart, product_id=product_id
        )

        cart_item.delete()

        return Response(
            {'success': 'Product removed from cart.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        cart = request.user.shopping_cart
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is already empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart.items.all().delete()

        return Response(
            {'success': 'Cart cleared.'},
            status=status.HTTP_204_NO_CONTENT
        )
