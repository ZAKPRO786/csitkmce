from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    department = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    year = models.IntegerField()

    def __str__(self):
        return self.user.username

class Event(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateTimeField()
    registration_fee = models.DecimalField(max_digits=6, decimal_places=2)
    photo = models.ImageField(upload_to='event_photos/', blank=True, null=True)
    max_participants = models.IntegerField(null=True, blank=True)  # Optional field to limit registrations
    is_active = models.BooleanField(default=True)  # To mark if event is still open for registration

    def __str__(self):
        return self.name
class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    payment_status = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    registration_date = models.DateTimeField(auto_now_add=True)  # Timestamp for when the student registered
    payment_method = models.CharField(max_length=50, choices=[('Razorpay', 'Razorpay'), ('PhonePe', 'PhonePe')], blank=True, null=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.event.name}"

