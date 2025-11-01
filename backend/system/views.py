from django.views.generic import TemplateView


class LandingView(TemplateView):
    template_name = "system/landing.html"


class DashboardView(TemplateView):
    template_name = "system/dashboard.html"
    required_roles = ["ADMIN"]


class PointOfSaleView(TemplateView):
    template_name = "system/pos.html"
    required_roles = ["CASHIER", "ADMIN"]
