from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('rental/ready/', views.RentalReadyView.as_view(), name='rental_ready'),
    path('rental/', views.RentalView.as_view(), name='rental'),
    path('rental/confirm/', views.RentalConfirmView.as_view(), name='rental_confirm'),
    path('rental/checkout/', views.RentalCheckoutView.as_view(), name='rental_checkout'),
    path('rental/complete/', views.RentalCompleteView.as_view(), name='rental_complete'),
    path('rental/complete/social/', views.RentalCompleteSocialView.as_view(), name='rental_complete_social'),
]
