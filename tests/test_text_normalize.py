from app.services.text_normalize import clean_user_text, normalize_text, search_tokens


def test_cyrillic_and_latin_match():
    assert normalize_text("Ўтган кунлар") == normalize_text("O‘tgan kunlar") == "otgan kunlar"


def test_apostrophe_variants_equal():
    variants = ["G'alaba", "Gʻalaba", "G`alaba", "G’alaba", "Galaba"]
    assert {normalize_text(v) for v in variants} == {"galaba"}


def test_empty_and_symbols():
    assert normalize_text(None) == ""
    assert normalize_text("  !!! ") == ""
    assert normalize_text("«Mehrobdan  chayon»!") == "mehrobdan chayon"


def test_search_tokens_longest_first_unique():
    assert search_tokens("Abdulla Qodiriy - O'tgan kunlar kunlar") == ["abdulla", "qodiriy", "kunlar"]


def test_clean_user_text_strips_control_chars_and_limits():
    assert clean_user_text("a\x00b\nc  d", 10) == "abc d"
    assert clean_user_text("x" * 50, 5) == "xxxxx"
