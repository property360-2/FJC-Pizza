import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_landing_accessible(client):
    response = client.get(reverse("system:landing"))
    assert response.status_code == 200
    assert b"Sign in" in response.content


@pytest.mark.django_db
def test_pos_accessible_for_cashier(client):
    cashier = User.objects.create_user(
        username="cashier",
        password="strong-pass",
        role=User.Roles.CASHIER,
    )

    client.login(username="cashier", password="strong-pass")
    response = client.get(reverse("system:pos"))

    assert response.status_code == 200
    assert b"Point of Sale" in response.content
