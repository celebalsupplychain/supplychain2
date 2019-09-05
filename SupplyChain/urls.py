from django.urls import path
from . import views
from django.views.generic.base import RedirectView



urlpatterns = [path('get_data', views.SupplyChain.as_view()),
               path('uniqueid', views.random_id),
               path('storage_verify', views.azure_functions.as_view()),
               path('', views.index.as_view())]
