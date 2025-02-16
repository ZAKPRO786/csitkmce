from django.urls import path
from .import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # HTML Views
    path('',views.show_index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logou/', views.user_logout, name='logout'),
    path('sample/', views.Leaderboard, name='Leader'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('event/register/<int:event_id>/', views.register_event, name='register_event'),
   path('download/registrations/<str:file_type>/', views.download_registration_data, name='download_registration_data'),
   path('registration/success/', views.registration_success, name='registration_success'),
    path('create_order/', views.create_order, name='create_order'),
    path('verify_payment/', views.verify_payment, name='verify_payment'),
    path('razor/', views.razorpayment, name='razor'),

    # REST API Views
    path('api/register-student/', views.register_student_api, name='register_student_api'),
    path('api/events/', views.list_events_api, name='list_events_api'),
    path('api/event/register/<int:event_id>/', views.register_event_api, name='register_event_api'),
]

if settings.DEBUG:
    urlpatterns +=static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
    urlpatterns +=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)