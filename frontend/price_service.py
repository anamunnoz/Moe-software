from price.price import calculate_price
import json

with open('./price/fabrication.json', 'r', encoding='utf-8') as f:
    costs = json.load(f)


class PriceService:
    @staticmethod
    def calculate_book_price(book_data, additives_data, discount=0, quantity=1):
        """
        Calcula el precio de un libro según la fórmula:
        ((precio_base + precio_caratula) - descuento) + precio_servicio
        
        Args:
            book_data: dict con datos del libro (debe tener 'number_pages')
            additives_data: lista de aditivos del libro
            discount: descuento en porcentaje (0-100)
            quantity: cantidad de libros
        
        Returns:
            float: precio total del libro
        """
        # 1. Precio base (número de páginas)

        number_of_pages = book_data.get('number_pages', 0)
        color_pages = book_data.get("color_pages", 0)
        printing_format = book_data.get("printing_format", "Normal")
        base_price = calculate_price(number_of_pages, color_pages, printing_format, costs)
        
        # 2. Buscar carátula y servicio en los aditivos
        cover_price = 0
        service_price = 0
        
        for additive in additives_data:
            name_lower = additive['name'].lower().strip()
            price = additive.get('price', 0)
            
            if name_lower.startswith('carátula'):
                cover_price = price
            elif name_lower.startswith('servicio'):
                service_price = price
        
        # 3. Aplicar fórmula: ((base + carátula) - descuento) + servicio
        subtotal = base_price + cover_price
        subtotal_after_discount = subtotal * (1 - discount / 100.0)
        final_price_per_book = subtotal_after_discount + service_price
        
        # 4. Aplicar cantidad
        total_price = final_price_per_book * quantity
        
        return round(total_price, 2)
    
    @staticmethod
    def calculate_order_price(selected_books, books_data, additives_data, delivery_price=0):
        """
        Calcula el precio total de una orden
        
        Args:
            selected_books: lista de libros seleccionados en la orden
            books_data: lista completa de libros disponibles
            additives_data: lista completa de aditivos disponibles
            delivery_price: precio del delivery
        
        Returns:
            dict: {
                'total_price': float,
                'books_prices': list,  # precios individuales de cada libro
                'delivery_price': float,
                'final_total': float
            }
        """
        total_price = 0
        books_prices = []
        
        for book_entry in selected_books:
            # Buscar el libro en los datos disponibles
            book_id = book_entry.get('book_id')
            book_data = None
            
            for book in books_data:
                if book['idBook'] == book_id:
                    book_data = book
                    break
            
            if not book_data:
                continue
            
            # Obtener aditivos específicos de este libro
            book_additives = []
            for add_id in book_entry.get('additives', []):
                for additive in additives_data:
                    if additive['idAdditive'] == add_id:
                        book_additives.append(additive)
                        break
            
            # Calcular precio del libro
            book_price = PriceService.calculate_book_price(
                book_data=book_data,
                additives_data=book_additives,
                discount=book_entry.get('discount', 0),
                quantity=book_entry.get('quantity', 1)
            )
            
            books_prices.append({
                'book_id': book_id,
                'title': book_entry.get('title', ''),
                'price': book_price,
                'quantity': book_entry.get('quantity', 1)
            })
            
            total_price += book_price
        
        return {
            'total_price': round(total_price, 2),
            'books_prices': books_prices,
            'delivery_price': round(delivery_price, 2),
        }
    
    @staticmethod
    def calculate_outstanding_payment(total_price, payment_advance):
        """Calcula el pago pendiente"""
        try:
            payment_advance = float(payment_advance or 0)
        except ValueError:
            payment_advance = 0.0
        
        outstanding = max(0, total_price - payment_advance)
        return round(outstanding, 2)