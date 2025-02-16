from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Student, Event, Registration

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = ['id', 'user', 'phone_number', 'department', 'batch', 'year']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'description', 'date', 'registration_fee']

class RegistrationSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    event = EventSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ['id', 'student', 'event', 'payment_status', 'phonepe_order_id']
