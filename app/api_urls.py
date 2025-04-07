from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import CustomerViewSet, CoffeeMillingViewSet, PaymentViewSet, CurrentUserView, DashboardStatsView

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'coffee-milling', CoffeeMillingViewSet, basename='coffee-milling')
router.register(r'payments', PaymentViewSet, basename='payment')

# Wire up our API using the router's URLs
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]
