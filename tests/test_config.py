import pytest
from pydantic import ValidationError

from app.config import Settings


def _url(value: str) -> str:
    return Settings(database_url=value).database_url


def test_railway_url_converted_to_async_driver():
    assert _url("postgresql://u:p@h:5432/db") == "postgresql+asyncpg://u:p@h:5432/db"
    assert _url("postgres://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"


def test_quotes_and_spaces_are_cleaned():
    assert _url('  "postgresql://u:p@h/db"  ') == "postgresql+asyncpg://u:p@h/db"
    assert _url("'postgresql://u:p@h/db'") == "postgresql+asyncpg://u:p@h/db"


def test_sqlite_untouched():
    assert _url("sqlite+aiosqlite:///./x.db") == "sqlite+aiosqlite:///./x.db"


@pytest.mark.parametrize("value, hint", [
    ("", "bo'sh"),
    ('  ""  ', "bo'sh"),
    ("${{Postgres.DATABASE_URL}}", "hal qilinmadi"),
    ("localhost:5432/db", "noto'g'ri formatda"),
])
def test_bad_values_give_clear_message(value, hint):
    with pytest.raises(ValidationError) as info:
        Settings(database_url=value)
    assert hint in str(info.value)


def test_password_not_leaked_in_error():
    with pytest.raises(ValidationError) as info:
        Settings(database_url="user:SuperSecret123@host/db")
    assert "SuperSecret123" not in str(info.value)
