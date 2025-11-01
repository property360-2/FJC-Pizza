from django.urls import path

from .views import DashboardView, LandingView, PointOfSaleView

app_name = "system"

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("pos/", PointOfSaleView.as_view(), name="pos"),
]
