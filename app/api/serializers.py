from rest_framework import serializers
from app.models import Customer, CoffeeMilling, Payment
from accounts.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number', 'address', 'profile_picture']

class CustomerSerializer(serializers.ModelSerializer):
    registered_by = serializers.ReadOnlyField(source='registered_by.username')

    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'gender', 'registered_at', 'registered_by']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['registered_by'] = request.user
        return super().create(validated_data)


class CoffeeMillingSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    total_cost = serializers.ReadOnlyField()
    registered_by = serializers.ReadOnlyField(source='registered_by.username')

    class Meta:
        model = CoffeeMilling
        fields = "__all__"

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['registered_by'] = request.user
        return super().create(validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    milling_record_details = CoffeeMillingSerializer(source='milling_record', read_only=True)
    registered_by = serializers.ReadOnlyField(source='registered_by.username')

    class Meta:
        model = Payment
        fields = ['customer', 'customer_name', 'milling_record', 'milling_record_details', 
                  'amount_paid', 'payment_method', 'payment_status', 'paid_at', 'registered_by']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['registered_by'] = request.user
        return super().create(validated_data)
