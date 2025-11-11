from django.db import models

class Client(models.Model):
    idClient = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50)
    identity = models.CharField(max_length= 20)

    def __str__(self):
        return self.name


class Delivery(models.Model):
    idDelivery = models.AutoField(primary_key=True)
    zone = models.CharField(max_length=100)
    price = models.FloatField()
    description = models.TextField()

    def __str__(self):
        return self.zone
    
class Book(models.Model):
    idBook = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    number_pages = models.IntegerField()
    printing_format = models.CharField(max_length=100)
    color_pages = models.IntegerField()

    def __str__(self):
        return self.title
    
class Additive(models.Model):
    idAdditive = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.FloatField()

    def __str__(self):
        return self.name
    
class Requested_book(models.Model):
    idRequested_book = models.AutoField(primary_key=True)
    idBook = models.ForeignKey(Book, on_delete=models.CASCADE)

    def __str__(self):
        return self.idBook.title
    
class Order(models.Model):
    idOrder = models.AutoField(primary_key=True)
    _type = models.CharField(max_length=100, default = 'Regular')
    address = models.TextField(null=True, blank=True)
    idDelivery = models.ForeignKey(Delivery, on_delete=models.CASCADE)
    idClient = models.ForeignKey(Client, on_delete=models.CASCADE)
    order_date = models.CharField(max_length=10)
    delivery_date = models.CharField(max_length=10)
    total_price = models.FloatField()
    pay_method = models.CharField(max_length= 100)
    done = models.BooleanField()
    payment_advance = models.FloatField()
    outstanding_payment = models.FloatField()
    Requested_book = models.ManyToManyField(Requested_book, through='Book_on_order')
    added_to_excel = models.BooleanField(default=False)
    

    def save(self, *args, **kwargs):
        self.outstanding_payment = round(self.total_price - self.payment_advance, 2)
        if self.outstanding_payment < 0:
            self.outstanding_payment = 0
        super().save(*args, **kwargs)

class Book_on_order(models.Model):
    idRequested_book = models.ForeignKey(Requested_book, on_delete=models.CASCADE)
    idOrder = models.ForeignKey(Order, on_delete=models.CASCADE)
    discount = models.FloatField()
    ready = models.BooleanField()
    quantity = models.IntegerField()


class Requested_book_additive(models.Model):
    idRequested_book = models.ForeignKey(Requested_book, on_delete=models.CASCADE)
    idAdditive = models.ForeignKey(Additive, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.idRequested_book.idBook.title} + {self.idAdditive.name}"

class Production_costs(models.Model):
    idProduction_costs = models.AutoField(primary_key=True)
    product = models.CharField(max_length=100)
    product_price = models.FloatField()
