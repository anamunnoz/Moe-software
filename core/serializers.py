from rest_framework import serializers
from django.db import transaction
from .models import (
    Client,
    Delivery,
    Book,
    Additive,
    Requested_book,
    Book_on_order,
    Order,
    Requested_book_additive,
    Production_costs
)

#? ----------------------------
#? Client
#? ----------------------------
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['idClient', 'name', 'phone_number', 'identity']

#? ----------------------------
#? Delivery
#? ----------------------------
class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['idDelivery', 'zone', 'price', 'description']

    def validate(self, attrs):
        zone = attrs.get('zone', None)
        if not self.instance and zone:
            if Delivery.objects.filter(zone__iexact=zone).exists():
                raise serializers.ValidationError({'zone': 'A delivery with this zone already exists.'})
        if self.instance and 'zone' in attrs:
            new_zone = attrs['zone']
            if Delivery.objects.filter(zone__iexact=new_zone).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError({'zone': 'Another delivery with this zone already exists.'})
        return attrs

#? ----------------------------
#? Book
#? ----------------------------
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['idBook', 'title', 'author', 'number_pages', 'printing_format', 'color_pages']

    def validate(self, attrs):
        if self.instance:
            new_title = attrs.get('title', self.instance.title)
            new_author = attrs.get('author', self.instance.author)
        else:
            new_title = attrs.get('title')
            new_author = attrs.get('author')

        if new_title and new_author:
            qs = Book.objects.filter(title__iexact=new_title, author__iexact=new_author)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('A book with the same title and author already exists.')
        return attrs

#? ----------------------------
#? Additive
#? ----------------------------
class AdditiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Additive
        fields = ['idAdditive', 'name', 'price']

    def validate(self, attrs):
        name = attrs.get('name') if not self.instance else attrs.get('name', self.instance.name)
        if name:
            qs = Additive.objects.filter(name__iexact=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({'name': 'An additive with this name already exists.'})
        return attrs

#? ----------------------------
#? RequestedBook + Additives
#? ----------------------------
class RequestedBookAdditiveSerializer(serializers.ModelSerializer):
    idRequested_book_title = serializers.CharField(source='idRequested_book.idBook.title', read_only=True)
    idAdditive_name = serializers.CharField(source='idAdditive.name', read_only=True)

    class Meta:
        model = Requested_book_additive
        fields = [
            'id',
            'idRequested_book',
            'idAdditive',
            'idRequested_book_title',
            'idAdditive_name'
        ]


class RequestedBookSerializer(serializers.ModelSerializer):
    idBook_title = serializers.CharField(source='idBook.title', read_only=True)
    additives = serializers.PrimaryKeyRelatedField(
        queryset=Additive.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Requested_book
        fields = ['idRequested_book', 'idBook', 'idBook_title', 'additives']

#? ----------------------------
#? BookOnOrder
#? ----------------------------
class BookOnOrderSerializer(serializers.ModelSerializer):
    idRequested_book_title = serializers.CharField(source='idRequested_book.idBook.title', read_only=True)
    idOrder_type = serializers.CharField(source='idOrder.__type', read_only=True)

    class Meta:
        model = Book_on_order
        fields = ['id', 'idRequested_book', 'idOrder', 'discount', 'ready', 'idRequested_book_title', 'idOrder__type', "quantity"]

#? ----------------------------
#? Order 
#? ----------------------------
class OrderSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='idClient.name', read_only=True)
    delivery_name = serializers.CharField(source='idDelivery.zone', read_only=True)
    requested_books = RequestedBookSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'idOrder',
            '_type',
            'address',
            'idDelivery',
            'delivery_name',
            'idClient',
            'client_name',
            'order_date',
            'delivery_date',
            'total_price',
            'pay_method',
            'done',
            'payment_advance',
            'outstanding_payment',
            'requested_books',
            'added_to_excel'
        ]

    @transaction.atomic
    def create(self, validated_data):
        requested_books_data = validated_data.pop('requested_books', [])
        order = Order.objects.create(**validated_data)
        return order

class ProductionCostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Production_costs
        fields = ['idProduction_costs', 'product', 'product_price']
