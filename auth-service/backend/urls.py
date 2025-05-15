from django.urls import path
from .views import RegisterView, CustomLoginView, UserFullList, UserZoneUpdate

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view()),
    path("users/", UserFullList.as_view()),
    path("users/<int:pk>/zone/", UserZoneUpdate.as_view()),  # ← NEW
]
