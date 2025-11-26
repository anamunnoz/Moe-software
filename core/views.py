from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Client, Delivery, Book, Additive, Requested_book, Book_on_order, Order, Requested_book_additive, Production_costs 
from .serializers import ClientSerializer, DeliverySerializer, BookSerializer, AdditiveSerializer, RequestedBookSerializer, BookOnOrderSerializer, OrderSerializer, RequestedBookAdditiveSerializer, ProductionCostsSerializer
from django.db import transaction
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta, date
from django.utils import timezone
from collections import Counter


#? ----------------------------
#? ClientViewSet
#? ----------------------------
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        name = request.query_params.get('name')
        identity = request.query_params.get('identity')
        if name:
            qs = qs.filter(name__icontains=name)
        if identity:
            qs = qs.filter(identity__iexact=identity)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='search_with_orders')
    def search_with_orders(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {"error": "El parámetro 'q' es requerido"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        clients = Client.objects.filter(
            Q(name__icontains=query) |
            Q(identity__icontains=query) |
            Q(phone_number__icontains=query)
        ).distinct()

        if not clients.exists():
            return Response({"clients": []}, status=status.HTTP_200_OK)

        result = []
        for client in clients:
            orders = Order.objects.filter(idClient=client).select_related('idDelivery')
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'idOrder': order.idOrder,
                    '_type': order._type,
                    'address': order.address,
                    'delivery_zone': order.idDelivery.zone if order.idDelivery else None,
                    'delivery_price': order.idDelivery.price if order.idDelivery else 0,
                    'order_date': order.order_date,
                    'delivery_date': order.delivery_date,
                    'total_price': order.total_price,
                    'pay_method': order.pay_method,
                    'done': order.done
                })

            unique_addresses = set()
            for order in orders:
                if order.address and order.address.strip():
                    unique_addresses.add(order.address.strip())
            
            client_data = {
                'idClient': client.idClient,
                'name': client.name,
                'phone_number': client.phone_number,
                'identity': client.identity,
                'total_orders': orders.count(),
                'unique_addresses': list(unique_addresses),
                'orders': orders_data
            }
            
            result.append(client_data)

        return Response({"clients": result}, status=status.HTTP_200_OK)

#? ----------------------------
#? DeliveryViewSet
#? ----------------------------
class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer

    def create(self, request, *args, **kwargs):
        zone = request.data.get("zone")
        description = request.data.get("description")
        price = request.data.get("price")

        existing = Delivery.objects.filter(zone__iexact=zone).first()
        if existing:
            serializer = self.get_serializer(existing)
            return Response({
                "error": "exists",
                "zone": existing.zone,
                "price": existing.price,
                "description": existing.description
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        zone = request.query_params.get('zone')
        if zone:
            qs = qs.filter(zone__icontains=zone)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='delete_by_zone')
    def delete_by_zone(self, request):
        zone = request.query_params.get('zone')
        if not zone:
            return Response({'Error': 'El parámetro zona es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(zone__iexact=zone)
        deleted_count = qs.count()
        qs.delete()
        return Response({'Eliminado': deleted_count})

    @action(detail=False, methods=['patch'], url_path='update_price_by_zone')
    def update_price_by_zone(self, request):
        zone = request.data.get('zone') or request.query_params.get('zone')
        price = request.data.get('price')
        if zone is None or price is None:
            return Response({'Error': 'Zona y precio son requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            price = float(price)
        except ValueError:
            return Response({'Error': 'El precio debe ser un número'}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(zone__iexact=zone)
        updated = qs.update(price=price)
        serializer = self.get_serializer(qs, many=True)
        return Response({'Actualizado': updated, 'objects': serializer.data})

#? ----------------------------
#? BookViewSet
#? ----------------------------
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        title = request.query_params.get('title')
        author = request.query_params.get('author')
        if title:
              qs = qs.filter(title__icontains=title)
        if author:
             qs = qs.filter(author__icontains=author)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='delete_by_title')
    def delete_by_title(self, request):
        title = request.query_params.get('title')
        if not title:
            return Response({'Error': 'El título es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(title__icontains=title)
        deleted = qs.count()
        qs.delete()
        return Response({'Libro eliminado': deleted})

    @action(detail=False, methods=['delete'], url_path='delete_by_author')
    def delete_by_author(self, request):
        author = request.query_params.get('author')
        if not author:
            return Response({'Error': 'El párametro autor es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(author__icontains=author)
        deleted = qs.count()
        qs.delete()
        return Response({'Eliminado': deleted})

    @action(detail=False, methods=['patch'], url_path='update_pages_by_title')
    def update_pages_by_title(self, request):
        title = request.data.get('title') or request.query_params.get('title')
        pages = request.data.get('number_pages')
        if title is None or pages is None:
            return Response({'Error': 'Título y número de páginas es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pages = int(pages)
        except ValueError:
            return Response({'Error': 'El número de páginas debe ser un número entero'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(title__icontains=title)
        updated = qs.update(number_pages=pages)
        serializer = self.get_serializer(qs, many=True)
        return Response({'Libro actualizado': updated, 'objects': serializer.data})
        
    @action(detail=False, methods=['get'], url_path='get_price')
    def get_price(self, request):
        title = request.query_params.get('title')
        author = request.query_params.get('author')
        if not title or not author:
            return Response({'Error': 'Título y autor son requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(title__iexact=title, author__iexact=author)
        if not qs.exists():
            return Response({'Error': 'Libro no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        book = qs.first()
        return Response({'title': book.title, 'author': book.author, 'price': book.number_pages})
    
    @action(detail=False, methods=['get'], url_path='search_titles')
    def search_titles(self, request):
        query = request.query_params.get('query')
        if not query:
            return Response({'Error': 'query param required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(title__icontains=query)
        titles = list(qs.values_list('title', flat=True))
        return Response({'Resultado': titles})

    

#? ----------------------------
#? AdditiveViewSet
#? ----------------------------
class AdditiveViewSet(viewsets.ModelViewSet):
    queryset = Additive.objects.all()
    serializer_class = AdditiveSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        name = request.query_params.get('name')
        if name:
            qs = qs.filter(name__icontains=name)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='delete_by_name')
    def delete_by_name(self, request):
        name = request.query_params.get('name')
        if not name:
            return Response({'detail': 'name query param required'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(name__icontains=name)
        deleted = qs.count()
        qs.delete()
        return Response({'deleted': deleted})

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class RequestedBookViewSet(viewsets.ModelViewSet):
    queryset = Requested_book.objects.all()
    serializer_class = RequestedBookSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().select_related('idClient', 'idDelivery').prefetch_related('Requested_book__idBook')
    serializer_class = OrderSerializer

    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='create_full_order')
    def create_full_order(self, request):
        data = request.data

        order_serializer = self.get_serializer(data=data)
        order_serializer.is_valid(raise_exception=True)
        order = order_serializer.save()

        requested_books_data = data.get("requested_books", [])
        created_requested_books = []

        try:
            for rb in requested_books_data:
                requested_book_serializer = RequestedBookSerializer(data={"idBook": rb["idBook"]})
                requested_book_serializer.is_valid(raise_exception=True)
                requested_book = requested_book_serializer.save()
                additives = rb.get("additives", [])
                for add_id in additives:
                    additive_obj = Additive.objects.get(pk=add_id)
                    Requested_book_additive.objects.create(
                        idRequested_book=requested_book,
                        idAdditive=additive_obj
                    )
                    
                Book_on_order.objects.create(
                    idRequested_book=requested_book,
                    idOrder=order,
                    discount=rb.get("discount", 0),
                    ready=rb.get("ready", False),
                    quantity = rb.get("quantity", 1),
                    base_price=rb.get("base_price")
                )

                created_requested_books.append(requested_book.idRequested_book)
        except Exception as e:
            transaction.set_rollback(True)
            return Response(
                {"detail": f"Error creando libros o aditivos: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "order": order_serializer.data,
            "requested_books": created_requested_books,
        }, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    @action(detail=True, methods=['delete'], url_path='delete_full_order')
    def delete_full_order(self, request, pk=None):
        try:
            order = self.get_object()

            book_links = Book_on_order.objects.filter(idOrder=order)
            requested_books_ids = [bo.idRequested_book.idRequested_book for bo in book_links]           
            book_links.delete()
            Requested_book_additive.objects.filter(idRequested_book__in=requested_books_ids).delete()           
            Requested_book.objects.filter(idRequested_book__in=requested_books_ids).delete()    
            order.delete()

            return Response(
                {"detail": f"Orden {pk} y sus datos asociados eliminados correctamente."},
                status=status.HTTP_204_NO_CONTENT
            )

        except Order.DoesNotExist:
            return Response(
                {"detail": "Orden no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            transaction.set_rollback(True)
            return Response(
                {"detail": f"Error eliminando la orden: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
  
    @transaction.atomic
    @action(detail=False, methods=['delete'], url_path='delete_by_client')
    def delete_by_client(self, request):
        client_name = request.query_params.get("client_name")

        if not client_name:
            return Response(
                {"detail": "Debe enviar el parámetro ?client_name="},
                status=status.HTTP_400_BAD_REQUEST
            )

        orders = Order.objects.filter(idClient__name__icontains=client_name)

        if not orders.exists():
            return Response(
                {"detail": "No se encontraron órdenes para ese cliente."},
                status=status.HTTP_404_NOT_FOUND
            )

        count = orders.count()
        orders.delete()

        return Response(
            {"detail": f"Se eliminaron {count} órdenes del cliente {client_name}."},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['get'], url_path='full_details')
    def get_full_details(self, request, pk=None):
        try:
            order = self.get_queryset().get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "Orden no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        order_data = {
            "idOrder": order.idOrder,
            "_type": order._type,
            "address": order.address,
            "order_date": order.order_date,
            "delivery_date": order.delivery_date,
            "total_price": order.total_price,
            "pay_method": order.pay_method,
            "done": order.done,
            "payment_advance": order.payment_advance,
            "outstanding_payment": order.outstanding_payment,
            "added_to_excel": order.added_to_excel,
            "delivery_zone": order.idDelivery.zone if order.idDelivery else None,
            "delivery_price": order.idDelivery.price if order.idDelivery else 0,
            "discount": order.discount,
            "client": {
                "idClient": order.idClient.idClient,
                "name": order.idClient.name,
                "phone_number": order.idClient.phone_number,
                "identity": order.idClient.identity,
            },
            "books": []
        }

        book_links = (
            Book_on_order.objects
            .filter(idOrder=order)
            .select_related('idRequested_book__idBook')
        )

        for link in book_links:
            requested_book = link.idRequested_book
            book = requested_book.idBook

            additives = (
                Requested_book_additive.objects
                .filter(idRequested_book=requested_book)
                .select_related('idAdditive')
            )

            additives_data = [
                {
                    "idAdditive": add.idAdditive.idAdditive,
                    "name": add.idAdditive.name,
                    "price": add.additive_price
                }
                for add in additives
            ]

            order_data["books"].append({
                "idRequested_book": requested_book.idRequested_book,
                "book": {
                    "idBook": book.idBook,
                    "title": book.title,
                    "author": book.author,
                    "number_pages": book.number_pages,
                    "printing_format": book.printing_format,
                    "color_pages": book.color_pages
                },
                "additives": additives_data,
                "discount": link.discount,
                "ready": link.ready,
                "quantity": link.quantity,
                "base_price": link.base_price
            })

        return Response(order_data, status=status.HTTP_200_OK)


    @transaction.atomic
    @action(detail=True, methods=['put'], url_path='update_order_data')
    def update_order_data(self, request, pk=None):
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            return Response({"error": "Orden no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        allowed_fields = [
            'address', 'pay_method', '_type', 'payment_advance',
            'total_price', 'idDelivery', 'done', 'added_to_excel',
            'discount'
        ]
        update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        current_type = order._type

        for field, value in update_data.items():
            if field == "idDelivery" and value:
                try:
                    delivery = Delivery.objects.get(pk=value)
                    setattr(order, field, delivery)
                except Delivery.DoesNotExist:
                    continue
            else:
                setattr(order, field, value)

        new_type = update_data.get("_type")
        if new_type and new_type != current_type:
            self._update_order_type_additives(order, new_type)
            self._recalculate_delivery_date(order, new_type)

        try:
            payment_advance = float(order.payment_advance or 0)
            total_price = float(order.total_price or 0)
        except ValueError:
            payment_advance = 0.0
            total_price = 0.0

        order.outstanding_payment = round(max(total_price - payment_advance, 0), 2)

        order.save()

        serializer = self.get_serializer(order)
        return Response({
            "order": serializer.data,
            "detail": "Datos de la orden actualizados correctamente"
        }, status=status.HTTP_200_OK)


    
    def _recalculate_delivery_date(self, order, order_type: str):

        today = date.today()
        tipo = order_type.strip().lower()

        if tipo == "servicio regular":
            fecha_entrega = today + timedelta(days=30)

        elif tipo in ("servicio express", "servicio premium express"):
            objetivo = 7 if tipo == "servicio express" else 2
            dias_habiles = 0
            fecha_entrega = today

            while dias_habiles < objetivo:
                fecha_entrega += timedelta(days=1)
                if fecha_entrega.weekday() < 5:
                    dias_habiles += 1

        else:
            fecha_entrega = today + timedelta(days=30)

        order.delivery_date = fecha_entrega.strftime("%Y-%m-%d")
        order.save()



    @transaction.atomic
    @action(detail=True, methods=['patch'], url_path='update_ready_status')
    def update_ready_status(self, request, pk=None):
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            return Response({"error": "Orden no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        books_data = request.data.get("books", [])
        if not isinstance(books_data, list):
            return Response({"error": "Formato inválido para 'books'."}, status=status.HTTP_400_BAD_REQUEST)
        for b in books_data:
            book_id = b.get("idRequested_book")
            ready_status = b.get("ready", False)
            try:
                link = Book_on_order.objects.get(idRequested_book_id=book_id, idOrder=order)
                link.ready = ready_status
                link.save()
            except Book_on_order.DoesNotExist:
                continue

        all_ready = not Book_on_order.objects.filter(idOrder=order, ready=False).exists()
        order.done = all_ready
        order.save()

        return Response({"detail": "Estados actualizados correctamente", "done": order.done})
    
    def _update_order_type_additives(self, order: Order, new_type: str):
        current_type_lower = order._type.lower()
        new_type_lower = new_type.lower()
        book_links = Book_on_order.objects.filter(idOrder=order).select_related('idRequested_book')

        for link in book_links:
            requested_book = link.idRequested_book
            quantity = link.quantity

            old_additives = Requested_book_additive.objects.filter(
                idRequested_book=requested_book,
                idAdditive__name__istartswith="servicio"
            )
            for old in old_additives:
                order.total_price -= float(old.idAdditive.price) * quantity
            old_additives.delete()

            additive_to_add = None
            if new_type_lower.startswith("servicio express"):
                additive_to_add = "Servicio Express"
            elif new_type_lower.startswith("servicio premium express"):
                additive_to_add = "Servicio Premium Express"

            if additive_to_add:
                try:
                    additive_obj = Additive.objects.get(name__iexact=additive_to_add)
                    Requested_book_additive.objects.create(
                        idRequested_book=requested_book,
                        idAdditive=additive_obj,
                        precio_aditivo=additive_obj.price
                    )
                    order.total_price += float(additive_obj.price) * quantity
                except Additive.DoesNotExist:
                    continue

        order._type = new_type
        order.save()

  
class BookOnOrderViewSet(viewsets.ModelViewSet):
    queryset = Book_on_order.objects.all().select_related('idRequested_book__idBook', 'idOrder')
    serializer_class = BookOnOrderSerializer

class RequestedBookAdditiveViewSet(viewsets.ModelViewSet):
    queryset = Requested_book_additive.objects.select_related('idRequested_book__idBook', 'idAdditive').all()
    serializer_class = RequestedBookAdditiveSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        book_title = request.query_params.get('book_title')
        additive_name = request.query_params.get('additive_name')

        if book_title:
            qs = qs.filter(idRequested_book__idBook__title__icontains=book_title)
        if additive_name:
            qs = qs.filter(idAdditive__name__icontains=additive_name)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


#? ----------------------------
#? Estadísticas Dashboard
#? ----------------------------
class DashboardStatsViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'], url_path='main_stats')
    def main_stats(self, request):
        try:
            total_orders = Order.objects.count()
            total_clients = Client.objects.count()
            total_books_ordered = Book_on_order.objects.aggregate(total=Sum('quantity'))['total'] or 0

            today = timezone.now().date()
            current_year = today.year
            current_month = today.month
            month_str = str(current_month).zfill(2)

            month_orders_qs = Order.objects.filter(order_date__startswith=f"{current_year}-{month_str}")
            month_orders = month_orders_qs.count()
            month_income = month_orders_qs.aggregate(total=Sum('total_price'))['total'] or 0

            return Response({
                'total_orders': total_orders,
                'total_clients': total_clients,
                'month_orders': month_orders,
                'total_books_ordered': total_books_ordered,
                'month_income': round(month_income, 2)
            })
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo estadísticas: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='monthly_orders_chart')
    def monthly_orders_chart(self, request):
        try:
            today = timezone.now().date()
            current_year = today.year
            current_month = today.month
            month_str = str(current_month).zfill(2)
            orders = Order.objects.filter(
                order_date__startswith=f"{current_year}-{month_str}"
            ).values('order_date')

            daily_counts = {}
            for order in orders:
                try:
                    order_date = datetime.strptime(order['order_date'], '%Y-%m-%d').date()
                    day_str = order_date.strftime('%Y-%m-%d')
                    daily_counts[day_str] = daily_counts.get(day_str, 0) + 1
                except ValueError:
                    continue
            

            first_day_month = today.replace(day=1)
            if today.month == 12:
                last_day_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                last_day_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            
            chart_data = []
            current_date = first_day_month
            while current_date <= last_day_month:
                day_str = current_date.strftime('%Y-%m-%d')
                chart_data.append({
                    'date': day_str,
                    'orders': daily_counts.get(day_str, 0),
                    'day': current_date.day
                })
                current_date += timedelta(days=1)
            
            return Response({'chart_data': chart_data})
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo datos de gráfica: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='top_books_month')
    def top_books_month(self, request):
        try:
            today = timezone.now().date()
            current_year = today.year
            current_month = today.month
            month_str = str(current_month).zfill(2)
            book_orders = Book_on_order.objects.filter(
                idOrder__order_date__startswith=f"{current_year}-{month_str}"
            ).select_related('idRequested_book__idBook')

            book_counts = Counter()
            for book_order in book_orders:
                book_title = book_order.idRequested_book.idBook.title
                book_counts[book_title] += book_order.quantity

            top_books = book_counts.most_common(5)
            result = [{'book': book, 'orders': count} for book, count in top_books]
            
            return Response({'top_books': result})
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo top libros: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ProductionCostsViewSet(viewsets.ModelViewSet):
    queryset = Production_costs.objects.all()
    serializer_class = ProductionCostsSerializer

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        product = request.query_params.get('product')
        if product:
            qs = qs.filter(product__icontains=product)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], url_path='delete_by_product')
    def delete_by_product(self, request):
        product = request.query_params.get('product')
        if not product:
            return Response({'error': 'El parámetro "product" es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        qs = self.get_queryset().filter(product__icontains=product)
        deleted = qs.count()
        qs.delete()
        return Response({'deleted': deleted})

            