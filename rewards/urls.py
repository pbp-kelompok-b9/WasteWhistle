from django.urls import path

from WasteWhistle.views import *
from .views import *

app_name = "rewards"

urlpatterns = [
    path('', reward_list, name='reward_list'),
    path('<int:pk>/redeem/', redeem_reward, name='redeem_reward'),
    path('<int:pk>/ubah/', reward_update, name='reward_update'),
    path('<int:pk>/hapus/', reward_delete, name='reward_delete'),
    path('baru/', reward_create, name='reward_create'),
]