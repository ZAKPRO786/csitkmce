from django.contrib import admin
from django.contrib.auth.models import User
from .models import Student, Event, Registration
from django.contrib import admin
from django.http import HttpResponse
from .models import Registration
from .views import generate_excel_file, generate_pdf_file
# Customize StudentAdmin
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'department', 'batch', 'year',)
    search_fields = ('user__username', 'phone_number', 'department')
    list_filter = ('department', 'batch', 'year')

# Customize EventAdmin
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'registration_fee')
    search_fields = ('name',)
    list_filter = ('date',)
    ordering = ('-date',)

# Customize RegistrationAdmin



class RegistrationAdmin(admin.ModelAdmin):
    # Add your desired fields to list display
    list_display = ('student', 'event', 'payment_status', 'razorpay_order_id', 'get_registration_fee', 'registration_date', 'payment_method')

    # Add filters for payment status
    list_filter = ('payment_status',)

    # Add search functionality for student username and event name
    search_fields = ('student__user__username', 'event__name')

    # Add the custom download actions
    actions = ['download_as_excel', 'download_as_pdf']

    # Custom function to display registration fee in the admin list view
    def get_registration_fee(self, obj):
        return obj.event.registration_fee

    # Allow sorting by registration fee column
    get_registration_fee.admin_order_field = 'event__registration_fee'
    get_registration_fee.short_description = 'Registration Fee'

    # Action to download selected registrations as Excel
    def download_as_excel(self, request, queryset):
        response = generate_excel_file(queryset)
        return response

    download_as_excel.short_description = "Download selected registrations as Excel"

    # Action to download selected registrations as PDF
    def download_as_pdf(self, request, queryset):
        response = generate_pdf_file(queryset)
        return response

    download_as_pdf.short_description = "Download selected registrations as PDF"







# Register models with their custom Admin configurations
admin.site.register(Student, StudentAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Registration, RegistrationAdmin)

