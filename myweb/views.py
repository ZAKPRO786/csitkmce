
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import admin
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.conf import settings
from .models import Student, Event, Registration
from .forms import  UserRegistrationForm, UserLoginForm,PaymentForm
from .serializers import StudentSerializer, EventSerializer, RegistrationSerializer
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import openpyxl
import uuid
import os
def show_index(request):
    return render(request,"index.html")
# HTML Views
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Get user but don't save yet
            user.set_password(form.cleaned_data['password'])  # Hash password
            user.save()  # Now save the user

            # Create Student Profile
            student = Student.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                department=form.cleaned_data['department'],
                batch=form.cleaned_data['batch'],
                year=form.cleaned_data['year']
            )

            return redirect('login')  # Redirect after successful registration

    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})
def user_logout(request):
    logout(request)
    return redirect('login')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Event, Registration

@login_required
def dashboard(request):
    if request.user.is_staff:
        # Redirect to the Django admin interface for staff users
        return redirect('admin:index')

    # Fetch all events
    events = Event.objects.all()

    # Fetch registrations for the logged-in user
    registrations = Registration.objects.filter(student__user=request.user)

    # Create a dictionary of registered event IDs for easy lookup
    registered_event_ids = {registration.event.id for registration in registrations}

    return render(request, 'dashboard.html', {
        'events': events,
        'registered_event_ids': registered_event_ids,
    })

def Leaderboard(request):
    return render(request, 'sample.html')
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import uuid
import json
import razorpay
from .forms import PaymentForm
from .models import Event, Student, Registration

RAZORPAY_KEY_ID = ""
RAZORPAY_KEY_SECRET = ""

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
def register_event(request, event_id):
    # Get the event and student associated with the current logged-in user
    event = get_object_or_404(Event, id=event_id)
    student = get_object_or_404(Student, user=request.user)

    # Generate a unique order ID
    razorpay_order_id = str(uuid.uuid4())

    # Step 1: If registration fee is greater than 0, show payment form and integrate Razorpay
    if event.registration_fee > 0:
        if request.method == 'POST':
            form = PaymentForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']

                # Create Razorpay order
                order_amount = event.registration_fee * 100  # Convert ₹ to paise
                order_data = {
                    'amount': order_amount,
                    'currency': 'INR',
                    'receipt': razorpay_order_id,
                    'payment_capture': 1  # Auto-capture payment
                }
                order = razorpay_client.order.create(order_data)
                razorpay_order_id = order['id']

                # Return the payment page where user will confirm the payment
                return render(request, 'payment.html', {
                    'event': event,
                    'order_id': razorpay_order_id,
                    'form': form,
                    'amount': order_amount
                })

        else:
            form = PaymentForm()

        return render(request, 'payment.html', {
            'event': event,
            'order_id': razorpay_order_id,
            'form': form
        })
    else:
        # Registration is free, directly save the registration and redirect
        name = student.user.username  # Default name
        Registration.objects.create(
            student=student,
            event=event,
            payment_status=True,
            razorpay_order_id=razorpay_order_id
        )

        return redirect('registration_success')






# REST API Views
@api_view(['POST'])
def register_student_api(request):
    serializer = StudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def list_events_api(request):
    events = Event.objects.all()
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def register_event_api(request, event_id):
    student = request.user.student
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
    phonepe_order_id = str(uuid.uuid4())
    registration = Registration.objects.create(student=student, event=event, payment_status=False, phonepe_order_id=phonepe_order_id)
    serializer = RegistrationSerializer(registration)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
def registration_success(request):
    return render(request, 'registration_success.html')


import razorpay
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Event, Registration

def razorpayment(request):
    # Retrieve the amount and event_id from the query parameters
    amount = request.GET.get('amount', None)
    event_id = request.GET.get('event_id', None)

    if amount and event_id:
        try:
            # Convert amount to paise (1 INR = 100 paise)
            amount = int(float(amount) * 100)
            event = Event.objects.get(id=event_id)

            # Check if the user is already registered for this event
            if Registration.objects.filter(student=request.user.student, event=event).exists():
                messages.success(request, f"You are already registered for {event.name}.")
                return redirect('dashboard')  # Redirect to the dashboard if already registered

            if amount <= 0:
                # If amount is 0, automatically treat as successful registration
                registration = Registration.objects.create(
                    student=request.user.student,
                    event=event,
                    payment_status=True,  # Mark as successful registration
                    razorpay_order_id='auto-generated',  # Placeholder order ID
                )
                messages.success(request, f"You are successfully registered for {event.name}!")
                return redirect('dashboard')  # Return to the dashboard

            # If amount is greater than 0, create a Razorpay order
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

            # Create an order
            order = client.order.create({
                'amount': amount,  # Amount in paise
                'currency': 'INR',
                'payment_capture': '1'
            })

            # Get order ID
            order_id = order['id']
            logging.info(f"✅ Razorpay order created with ID: {order_id}")

            # 🔹 **Save Registration with order ID and pending payment**
            registration = Registration.objects.create(
                student=request.user.student,
                event=event,
                payment_status=False,  # Payment is pending
                razorpay_order_id=order_id,  # Store the Razorpay Order ID
            )
            logging.info(f"✅ Registration Created: {registration}")

            # Pass the order ID to the frontend
            context = {
                'order_id': order_id,
                'amount': amount / 100  # Convert back to INR for display
            }

            return render(request, 'razorpay.html', context)  # Show Razorpay payment page

        except Event.DoesNotExist:
            messages.error(request, "Event not found!")
            return redirect('dashboard')  # Go back to the dashboard if event is not found
        except Exception as e:
            logging.error(f"❌ An error occurred: {str(e)}")  # Log error for debugging
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('dashboard')  # Go back to the dashboard in case of any error

    else:
        return render(request, 'error.html', {'message': 'Amount or event ID not provided'})

import razorpay
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Initialize Razorpay Client
RAZORPAY_KEY_ID = ""
RAZORPAY_KEY_SECRET = ""

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@csrf_exempt
def create_order(request):
    """Create Razorpay Order"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            order_amount = int(data.get("amount", 500)) * 100  # Convert ₹ to paise
            order_currency = 'INR'
            order_receipt = 'order_rcptid_11'

            order_data = {
                'amount': order_amount,
                'currency': order_currency,
                'receipt': order_receipt,
                'payment_capture': 1  # 🔹 Change from '1' to integer 1
            }

            order = razorpay_client.order.create(order_data)
            return JsonResponse(order)
        except Exception as e:
            import traceback
            print("Error in create_order:", traceback.format_exc())  # 🔹 Debugging
            return JsonResponse({"error": str(e)}, status=400)


from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
import razorpay
import json
from .models import Event, Registration
from django.views.decorators.csrf import csrf_exempt




@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            logging.info(f"📥 Received Payment Verification Data: {data}")

            required_fields = ["razorpay_payment_id", "razorpay_order_id", "razorpay_signature"]
            if not all(k in data for k in required_fields):
                logging.error("❌ Missing required payment parameters")
                return JsonResponse({"error": "Missing payment parameters"}, status=400)

            # Extract values
            order_id = data["razorpay_order_id"]
            payment_id = data["razorpay_payment_id"]
            signature = data["razorpay_signature"]

            # Check if the order exists in the database
            try:
                registration = Registration.objects.get(razorpay_order_id=order_id)
                logging.info(f"✅ Found Registration: {registration}")

            except Registration.DoesNotExist:
                logging.error(f"❌ Registration not found for order ID: {order_id}")
                return JsonResponse({"error": "Registration not found"}, status=404)

            # Initialize Razorpay client
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

            # Verify the payment signature
            is_valid = client.utility.verify_payment_signature({
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature
            })

            if is_valid:
                logging.info("✅ Payment Verified Successfully!")

                # Update registration status
                registration.payment_status = True
                registration.save()

                messages.success(request, "Payment successful! You are now registered.")
                return JsonResponse({"status": "success", "redirect_url": "/dashboard/"})

            else:
                logging.error("❌ Invalid Payment Signature!")
                return JsonResponse({"error": "Invalid Payment Signature"}, status=400)

        except Exception as e:
            logging.error(f"❌ Error in verify_payment: {str(e)}")
            return JsonResponse({"error": "An error occurred while verifying the payment."}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Registration
from openpyxl import Workbook
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.utils import timezone


@staff_member_required
def download_registration_data(request, file_type):
    # Get all registrations data
    registrations = Registration.objects.all()

    if file_type == "excel":
        # Generate Excel file
        return generate_excel_file(registrations)
    elif file_type == "pdf":
        # Generate PDF file
        return generate_pdf_file(registrations)
    else:
        return HttpResponse("Invalid file type", status=400)


def generate_excel_file(registrations):
    # Create a workbook and sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Registrations"

    # Add headers
    headers = ["Student Name", "Event Name", "Payment Status", "PhonePe Order ID", "Registration Date",
               "Payment Method"]
    ws.append(headers)

    # Add registration data
    for registration in registrations:
        # Make registration date timezone-naive
        registration_date = registration.registration_date.replace(
            tzinfo=None) if registration.registration_date else None

        row = [
            registration.student.user.username,
            registration.event.name,
            "Paid" if registration.payment_status else "Pending",
            registration.phonepe_order_id,
            registration_date,
            registration.payment_method,
        ]
        ws.append(row)

    # Save the workbook to a memory buffer
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="registrations.xlsx"'

    # Save to the response buffer
    wb.save(response)
    return response


def generate_pdf_file(registrations):
    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="registrations.pdf"'

    # Create PDF object
    pdf = canvas.Canvas(response, pagesize=letter)

    # Set up title and formatting
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 750, f"Registrations Report (Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')})")

    y_position = 730  # Start position for writing content in PDF

    # Add headers
    headers = ["Student Name", "Event Name", "Payment Status", "PhonePe Order ID", "Registration Date",
               "Payment Method"]
    for i, header in enumerate(headers):
        pdf.drawString(100 + (i * 100), y_position, header)

    y_position -= 20  # Move down after headers

    # Add registration data
    for registration in registrations:
        pdf.drawString(100, y_position, registration.student.user.username)
        pdf.drawString(200, y_position, registration.event.name)
        pdf.drawString(300, y_position, "Paid" if registration.payment_status else "Pending")
        pdf.drawString(400, y_position, registration.phonepe_order_id or "-")
        pdf.drawString(500, y_position, registration.registration_date.strftime('%Y-%m-%d %H:%M:%S'))
        pdf.drawString(600, y_position, registration.payment_method or "-")

        y_position -= 20  # Move to next line

        # Check if page is full and add a new page if needed
        if y_position < 50:
            pdf.showPage()
            y_position = 750

    pdf.showPage()
    pdf.save()

    return response
