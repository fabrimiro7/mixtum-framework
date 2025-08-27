from django.urls import path
from . import views

urlpatterns = [
    path('subscriptions-add/', views.SubscriptionDetail.as_view(), name='subscription-add'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetail.as_view(), name='subscription-detail'),
    path('subscriptions-list/', views.SubscriptionList.as_view(), name='subscription-list'),
    path('subscription-put/<int:pk>/', views.SubscriptionDetail.as_view(), name='subscription-put'),

]
