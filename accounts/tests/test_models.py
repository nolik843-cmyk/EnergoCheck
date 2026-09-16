import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserRoles:
    def test_roles_include_only_consumer_and_employee(self):
        choices = dict(User.Role.choices)

        assert choices == {
            User.Role.CONSUMER: "Потребитель",
            User.Role.EMPLOYEE: "Сотрудник",
        }

    def test_consumer_user_has_expected_flags(self):
        user = User.objects.create_user(
            username="consumer_1",
            email="consumer@example.com",
            password="StrongPass123!",
            role=User.Role.CONSUMER,
        )

        assert user.role == User.Role.CONSUMER
        assert user.is_consumer is True
        assert user.is_employee is False

    def test_employee_user_has_expected_flags(self):
        user = User.objects.create_user(
            username="employee_1",
            email="employee@example.com",
            password="StrongPass123!",
            role=User.Role.EMPLOYEE,
        )

        assert user.role == User.Role.EMPLOYEE
        assert user.is_consumer is False
        assert user.is_employee is True
