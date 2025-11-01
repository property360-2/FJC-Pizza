from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView


class UserLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].widget.attrs.update(
            {"class": "form-control", "autofocus": True}
        )
        form.fields["password"].widget.attrs.update({"class": "form-control"})
        return form


class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"


class AccessDeniedView(TemplateView):
    template_name = "accounts/access_denied.html"
