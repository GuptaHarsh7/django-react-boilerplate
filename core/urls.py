from django.urls import path
from rest_framework.views import APIView
from . import views

app_name = 'core'

urlpatterns = [
    path('demo/', views.FileUplaodView.as_view(), name='file-upload-demo'),
    path('change-email/', views.ChangeEmailView.as_view(), name='change-email'),
    path('email/', views.EmailView.as_view(), name='email'),
    path('change-password/', views.ChangePasswordView.as_view(),
         name='change-passwords'),
    path('key/', views.APIKeyView.as_view(), name='api-key'),
    path('billing/', views.UserDetailsView.as_view(), name='billing'),
    #     path('test-payment/', views.test_payment, name='test-payment'),
    path('save-stripe-info/', views.save_stripe_info, name='save-info'),
    path('confirm-payment-intent/',
         views.confirm_payment_intent, name='confirm-payment'),
    path("cancel-subscription/", views.CancelSubscription.as_view(),
         name="cancel-subscription"),
    path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    path('upload/', views.ImageRecognitionView.as_view(), name='image-recognition'),

]
