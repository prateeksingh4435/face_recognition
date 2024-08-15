# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('api/save', views.save_user_data, name='save_user_data'),
    path('api/checkmatch', views.check_image_match, name='check_image_match'),
    path('api/edit_user_image', views.update_user_image, name='update_user_image'),
    path('save/', views.save_user_view, name='save_user_view'),
    path('check/', views.check_image_view, name='check_image_view'),
    
]
