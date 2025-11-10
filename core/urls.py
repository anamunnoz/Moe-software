# core/urls.py
from django.urls import path, include
from rest_framework import routers
from .views import (ClientViewSet, DeliveryViewSet, BookViewSet, AdditiveViewSet, RequestedBookViewSet, 
OrderViewSet, BookOnOrderViewSet, RequestedBookAdditiveViewSet, DashboardStatsViewSet)

router = routers.DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'books', BookViewSet, basename='book')
router.register(r'additives', AdditiveViewSet, basename='additive')
router.register(r'requested_books', RequestedBookViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'books_on_order', BookOnOrderViewSet)
router.register(r'requested_book_additives', RequestedBookAdditiveViewSet) 
router.register(r'dashboard', DashboardStatsViewSet, basename='dashboard')
router.register(r'production_costs', ProductionCostsViewSet, basename='production_costs')

urlpatterns = router.urls

urlpatterns = [
    path('', include(router.urls)),

]


