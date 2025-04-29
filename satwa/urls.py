from django.urls import path
from .views import *

app_name = 'satwa'

urlpatterns = [
    path('view-satwa/', view_satwa, name='view_satwa'),
    path('create-satwa/', create_satwa, name='create_satwa'),
    path('edit-satwa/<uuid:id>/', edit_satwa, name='edit_satwa'),
    path('delete-satwa/<uuid:id>/', delete_satwa, name='delete_satwa'),  
]