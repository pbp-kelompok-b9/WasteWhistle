from django.urls import path
 
from . import views
from .views import *
 
app_name = "rewards"
 
urlpatterns = [
    # Halaman
    path('', views.reward_list, name='reward_list'),
 
    # Endpoint JSON (GET)
    path('api/rewards/', views.get_rewards_json, name='get_rewards_json'),
    path('api/saya/', views.get_my_rewards_json, name='get_my_rewards_json'),
 
    # Endpoint AJAX (POST)
    path('api/rewards/baru/', views.create_reward_ajax, name='create_reward_ajax'),
    path('api/rewards/<int:pk>/ubah/', views.update_reward_ajax, name='update_reward_ajax'),
    path('api/rewards/<int:pk>/hapus/', views.delete_reward_ajax, name='delete_reward_ajax'),
    path('api/rewards/<int:pk>/tukar/', views.redeem_reward_ajax, name='redeem_reward_ajax'),
]
 