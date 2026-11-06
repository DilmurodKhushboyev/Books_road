import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.api.auth import InvalidInitData, validate_init_data

TOKEN = "123456:TEST-TOKEN"


def make_init_data(user_id=42, token=TOKEN, auth_date=None) -> str:
    fields = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "AAA",
        "user": json.dumps({"id": user_id, "first_name": "Ali"}, separators=(",", ":")),
    }
    check = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_valid_init_data():
    assert validate_init_data(make_init_data(7), TOKEN)["id"] == 7


def test_tampered_user_rejected():
    data = make_init_data(7).replace("%22id%22%3A7", "%22id%22%3A8")
    with pytest.raises(InvalidInitData):
        validate_init_data(data, TOKEN)


def test_wrong_token_rejected():
    with pytest.raises(InvalidInitData):
        validate_init_data(make_init_data(token="other:token"), TOKEN)


def test_expired_rejected():
    old = int(time.time()) - 3 * 24 * 3600
    with pytest.raises(InvalidInitData):
        validate_init_data(make_init_data(auth_date=old), TOKEN)


def test_empty_rejected():
    with pytest.raises(InvalidInitData):
        validate_init_data("", TOKEN)
