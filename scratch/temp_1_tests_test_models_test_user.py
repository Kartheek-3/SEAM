from src.models.user import User
import pytest

def test_user_model():
    user = User(
        id=1,
        name="John Doe",
        email="john.doe@example.com"
    )
    assert user.id == 1
    assert user.name == "John Doe"
    assert user.email == "john.doe@example.com"

def test_user_model_email_validation():
    with pytest.raises(ValueError):
        User(
            id=1,
            name="John Doe",
            email="invalid_email"
        )

def test_user_model_email_format():
    with pytest.raises(ValueError):
        User(
            id=1,
            name="John Doe",
            email="john.doe"
        )