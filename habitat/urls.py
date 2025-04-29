from django.urls import path
from .views import *

app_name = 'habitat'

urlpatterns = [
    path('view-habitat/', view_habitat, name='view_habitat'),
    path('detail-habitat/<str:nama>/', detail_habitat, name='detail_habitat'),
    path('create-habitat/', create_habitat, name='create_habitat'),
    path('edit-habitat/<str:nama>/', edit_habitat, name='edit_habitat'),
]
