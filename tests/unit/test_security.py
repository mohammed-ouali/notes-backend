import pytest
import jwt
from datetime import timedelta
from app.core.config import settings
from app.core.exceptions import TokenExpiredException, InvalidTokenException
from app.core.security import(
    get_password_hash,
    verify_password,
    decode_token,
    create_access_token,
    create_refresh_token
)


def test_password_hashing_success():
    plain_password = "SecretPassword"
    hashed_password = get_password_hash(plain_password)

    assert plain_password != hashed_password
    assert verify_password(plain_password=plain_password, hashed_password=hashed_password) is  True

def test_verify_password_failure():
    plain_password = "SecretPassword"
    wrong_password = "WrongPassword"
    hashed_password = get_password_hash(plain_password)

    assert verify_password(wrong_password, hashed_password) is False

def test_create_and_decode_access_token():
    subject = "user"
    token = create_access_token(subject=subject)

    assert isinstance(token, str)

    payload = decode_token(token, "access")
    assert payload["sub"] == "user"
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "iat" in payload

def test_create_and_decode_refresh_token():
    subject = "user"
    token = create_refresh_token(subject=subject)

    assert isinstance(token, str)

    payload = decode_token(token, "refresh")
    assert payload["sub"] == "user"
    assert payload["type"] == "refresh"
    assert "exp" in payload
    assert "iat" in payload

def test_decode_token_type_mismatched_raises_exception():
    token = create_access_token(subject="user")

    with pytest.raises(InvalidTokenException) as exception_info:
        decode_token(token, "refresh")
    expected_msg = "Invalid token type. Expected 'refresh', got 'access'"
    assert str(exception_info.value) == expected_msg

def test_decode_token_expired_raises_exception():
    expired_access_token = create_access_token("user", expire_delta=timedelta(seconds=-10))
    with pytest.raises(TokenExpiredException) as exception_info:
        decode_token(expired_access_token, expected_type="access")
    assert "Token has expired" in str(exception_info.value)

def test_decode_token_invalid_signature_raises_exception():
    invalid_token = create_access_token(subject="user") + "corruption"

    with pytest.raises(InvalidTokenException) as exception_info:
        decode_token(invalid_token, "access")
    assert "Invalid token signature or structure" in str(exception_info)

