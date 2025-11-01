from django.urls import path

from .views import AccessDeniedView, UserLoginView, UserLogoutView

app_name = "accounts"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("access-denied/", AccessDeniedView.as_view(), name="access_denied"),
]
