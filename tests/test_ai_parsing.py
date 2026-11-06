import pytest

from app.ai.base import AIError
from app.ai.parsing import parse_description, parse_detected_items, parse_match


def test_detected_items_valid_and_clamped():
    text = ('{"items":[{"title":"O\'tgan kunlar","author":"A. Qodiriy","kind":"book",'
            '"confidence":1.7,"quantity":0,"box_2d":[10,20,500,300]},'
            '{"title":"  ","kind":"book","confidence":0.5},'
            '{"title":"Atir","kind":"unknown_kind","confidence":0.4,"box_2d":[500,10,100,20]}]}')
    items = parse_detected_items(text)
    assert [i.title for i in items] == ["O'tgan kunlar", "Atir"]
    assert items[0].confidence == 1.0 and items[0].quantity == 1 and items[0].box == [10, 20, 500, 300]
    assert items[1].kind == "other" and items[1].box is None


def test_fenced_json_accepted():
    assert parse_detected_items('```json\n{"items": []}\n```') == []


def test_garbage_raises():
    with pytest.raises(AIError):
        parse_detected_items("bu JSON emas")
    with pytest.raises(AIError):
        parse_detected_items('{"no_items": 1}')


def test_description_not_found():
    assert parse_description('{"found": false}') is None
    assert parse_description('{"found": true, "title": "Joynamoz", "kind": "prayer_mat", "confidence": 0.8}').kind == "prayer_mat"


def test_match_out_of_range_is_none():
    assert parse_match('{"index": 5, "confidence": 0.9}', 3).index is None
    assert parse_match('{"index": -1, "confidence": 0.2}', 3).index is None
    assert parse_match('{"index": 2, "confidence": 0.9}', 3).index == 2
