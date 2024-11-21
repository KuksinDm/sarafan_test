import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from PIL import Image

from backend.constants import (
    MAX_NAME,
    MAX_SLUG,
    MIN_QUANTITY,
    PRICE_DECIMAL,
    PRICE_MAX,
    ZERO,
)

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=MAX_NAME,
                            unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=MAX_SLUG,
                            unique=True, verbose_name='Слаг')
    image = models.ImageField(upload_to='categories/',
                              verbose_name='Изображение категории')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=MAX_NAME, verbose_name='Название')
    slug = models.SlugField(max_length=MAX_SLUG,
                            unique=True, verbose_name='Слаг')
    category = models.ForeignKey(
        Category,
        related_name='subcategories',
        on_delete=models.CASCADE,
        verbose_name='Категория'
    )
    image = models.ImageField(upload_to='subcategories/',
                              verbose_name='Изображение подкатегории')

    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'

    def clean(self):
        if not self.category:
            raise ValidationError('Укажите категорию для подкатегории.')
        super().clean()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.category.name}"


class Product(models.Model):
    name = models.CharField(max_length=MAX_NAME, verbose_name='Название')
    slug = models.SlugField(max_length=MAX_SLUG,
                            unique=True, verbose_name='Слаг')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Категория'
    )
    subcategory = models.ForeignKey(
        Subcategory,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name='Подкатегория'
    )
    image = models.ImageField(
        upload_to='products/original/',
        verbose_name='Оригинальное изображение',
        default='products/original/default.jpg'
    )
    image_small = models.ImageField(
        upload_to='products/small/',
        blank=True,
        null=True,
        verbose_name='Маленькое изображение'
    )
    image_medium = models.ImageField(
        upload_to='products/medium/',
        blank=True,
        null=True,
        verbose_name='Среднее изображение'
    )
    image_large = models.ImageField(
        upload_to='products/large/',
        blank=True,
        null=True,
        verbose_name='Большое изображение'
    )
    price = models.DecimalField(max_digits=PRICE_MAX,
                                decimal_places=PRICE_DECIMAL)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def clean(self):
        if self.subcategory and self.subcategory.category != self.category:
            raise ValidationError('Подкатегория не соответствует '
                                  'выбранной категории.')
        if self.price <= ZERO:
            raise ValidationError('Цена должна быть больше нуля.')
        super().clean()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*args, **kwargs)

        if self.image and not kwargs.get('update_fields'):
            self._generate_resized_images()

    def _generate_resized_images(self):
        if self.image.name == 'products/default.jpg':
            return
        original_path = self.image.path

        sizes = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (800, 800),
        }

        resized_fields = []
        for size_name, size in sizes.items():
            if self._resize_image(original_path, size, size_name):
                resized_fields.append(f'image_{size_name}')

        if resized_fields:
            self.save(update_fields=resized_fields)

    def _resize_image(self, original_path, size, size_name):
        img = Image.open(original_path)
        img = img.convert('RGB')

        img.thumbnail(size, Image.LANCZOS)

        base_name = os.path.basename(os.path.splitext(self.image.name)[0])
        new_filename = f"{base_name}_{size_name}.jpg"
        new_path = os.path.join(settings.MEDIA_ROOT,
                                'products', size_name, new_filename)

        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        img.save(new_path, format='JPEG', quality=90)

        new_image_field = f'products/{size_name}/{new_filename}'
        if getattr(self, f'image_{size_name}') != new_image_field:
            setattr(self, f'image_{size_name}', new_image_field)
            return True
        return False

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Покупатель'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items',
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                default=MIN_QUANTITY,)
    quantity = models.PositiveIntegerField(default=MIN_QUANTITY,
                                           verbose_name='Количество')

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product'], name='unique_cart_item')
        ]

    def clean(self):
        if self.quantity < MIN_QUANTITY:
            raise ValidationError(
                {'quantity': 'Количество должно быть не меньше минимального.'})

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"
