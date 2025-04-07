from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from app.models import Customer, CoffeeMilling, Payment
from .serializers import CustomerSerializer, CoffeeMillingSerializer, PaymentSerializer, CustomUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime

# ✅ Customer ViewSet
class CustomerViewSet(viewsets.ModelViewSet):
    """Handle CRUD operations for Customers."""
    queryset = Customer.objects.all().order_by('-registered_at')
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """Automatically assign registered_by to the current user."""
        serializer.save(registered_by=self.request.user)


# ✅ Coffee Milling ViewSet
class CoffeeMillingViewSet(viewsets.ModelViewSet):
    """Handle CRUD operations for Coffee Milling records."""
    queryset = CoffeeMilling.objects.all().order_by('-milling_date')
    serializer_class = CoffeeMillingSerializer
    permission_classes = [IsAuthenticated]


# ✅ Payment ViewSet
class PaymentViewSet(viewsets.ModelViewSet):
    """Handle CRUD operations for Payment records."""
    queryset = Payment.objects.all().order_by('-paid_at')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


# Current User
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the logged-in user
        user = request.user
        
        # Serialize user data
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)


# Dashboard

class DashboardStatsView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        # Basic counts
        total_customers = Customer.objects.count()
        total_millings = CoffeeMilling.objects.count()
        total_payments = Payment.objects.count()
        
        # Get today's date with time set to beginning of day
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Total money collected today
        total_money_collected = Payment.objects.filter(
            paid_at__gte=today,
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Total kilograms hulled today
        total_kgs_hulled = CoffeeMilling.objects.filter(
            milling_date__gte=today,
            milling_status='completed'
        ).aggregate(total=Sum('hulled_coffee_weight'))['total'] or 0
        
        return Response({
            "total_customers": total_customers,
            "total_millings": total_millings,
            "total_payments": total_payments,
            "daily_stats": {
                "total_money_collected": total_money_collected,
                "total_kgs_hulled": total_kgs_hulled,
                "date": today.date().isoformat()
            }
        })