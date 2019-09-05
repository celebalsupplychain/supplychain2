from django.urls import path
from . import views
from django.views.generic.base import RedirectView


favicon_view = RedirectView.as_view(url='/', permanent=True)

urlpatterns = [path('get_data', views.SupplyChain.as_view()),
               path('uniqueid', views.random_id),
               path('storage_verify', views.azure_functions.as_view()),
               path('', views.index.as_view()),
               path('favicon.ico', favicon_view)]
