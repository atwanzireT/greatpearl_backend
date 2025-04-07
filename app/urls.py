from django.urls import path
from .views import (
    index,
    CustomerListView, CustomerDetailView, CustomerCreateView,
    MillingListView, MillingCreateView,
    PaymentCreateView, PaymentListView, NotificationListView
)

urlpatterns = [
    # Home Page
    path("", index, name="home"),

    # Customer URLs
    path("app/customers/", CustomerListView.as_view(), name="customer_list"),
    path("app/customers/<int:pk>/", CustomerDetailView.as_view(), name="customer_detail"),
    path("app/customers/register/", CustomerCreateView.as_view(), name="customer_register"),

    # Milling URLs
    path("app/milling/", MillingListView.as_view(), name="milling_list"),
    path("app/milling/new/", MillingCreateView.as_view(), name="milling_create"),

    # Payment URLs
    path("app/payments/", PaymentListView.as_view(), name="payment_list"),
    path("app/payment/<int:milling_id>/", PaymentCreateView.as_view(), name="payment_create"),
    
    # Notification URLs
    path("app/notifications/<int:customer_id>/", NotificationListView.as_view(), name="notification_list"),
]
