from django.urls import path

from WasteWhistle.views import *
from rewards.views import *

app_name = "rewards"

urlpatterns = [
    path('', reward_list, name='reward_list'),
    path('<int:pk>/redeem/', redeem_reward, name='redeem_reward'),
]