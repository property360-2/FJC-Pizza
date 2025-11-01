import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


def test_user_role_helpers():
    user = User(username="cashier", role=User.Roles.CASHIER)
    admin = User(username="admin", role=User.Roles.ADMIN)

    assert user.is_cashier() is True
    assert user.is_admin() is False
    assert admin.is_admin() is True
    assert admin.is_cashier() is False


@pytest.mark.django_db
def test_login_flow(client):
    user = User.objects.create_user(
        username="manager",
        password="strong-pass",
        role=User.Roles.ADMIN,
    )

    response = client.post(
        reverse("accounts:login"),
        {"username": "manager", "password": "strong-pass"},
        follow=True,
    )

    assert response.wsgi_request.user.is_authenticated
    assert response.wsgi_request.user.role == User.Roles.ADMIN
    assert response.status_code == 200


@pytest.mark.django_db
def test_middleware_blocks_wrong_role(client):
    cashier = User.objects.create_user(
        username="cashier",
        password="strong-pass",
        role=User.Roles.CASHIER,
    )

    client.login(username="cashier", password="strong-pass")
    response = client.get(reverse("system:dashboard"))

    # Middleware should redirect to the access denied page
    assert response.status_code == 302
    assert reverse("accounts:access_denied") in response.url
