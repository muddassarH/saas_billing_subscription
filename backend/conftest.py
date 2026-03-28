import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="u@test.com", password="testpass1234")


@pytest.fixture
def admin_user(db):
    from accounts.models import UserRole

    return User.objects.create_user(
        email="admin@test.com",
        password="testpass1234",
        role=UserRole.ADMIN,
        is_staff=True,
    )
