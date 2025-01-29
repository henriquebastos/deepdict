# Python imports
import datetime
import decimal
import re
from decimal import Decimal
from uuid import UUID

# Pip imports
import arrow
import pytest

# Internal imports
from dictdeeper.core import DeepDict
from dictdeeper.exceptions import (
    MatcherDatetimeMismatch,
    MatcherKeysDoNotMatch,
    MatcherLengthTooLong,
    MatcherLengthTooShort,
    MatcherMissingRequiredKey,
    MatcherNoMatchFound,
    MatcherRegexMismatch,
    MatcherTypeMismatch,
    MatcherValueMismatch,
)
from dictdeeper.matcher import DictMatcher


@pytest.fixture
def raw_data():
    return {
        "1": "one",
        "2": {
            "a": "A",
            "b": {
                "i": "I",
                "ii": "II",
            },
        },
        "3": ["index0", "index1", "index2"],
        "4": [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}, {"id": 3, "name": "baz"}],
    }


class TestDeepMatcher:
    @pytest.fixture
    def data(self, raw_data):
        return DictMatcher(raw_data)

    def test_dictdeeper_convenience_method(self, raw_data):
        assert DeepDict(raw_data) == raw_data

    def test_matches_exact(self, data, raw_data):
        assert data == raw_data

    def test_matches_partial(self, data):
        assert data == {
            "1": "one",
            ...: ...,
        }
        assert data == {
            "1": ...,
            "2": {"a": "A", ...: ...},
            ...: ...,
        }

    def test_matches_regex(self, data):
        assert data == {
            "1": re.compile("^.n.$"),
            ...: ...,
        }

    def test_matches_uuid(self):
        assert DeepDict({"id": "2D2C131C-E2A2-4DEA-887A-A7A6678B71AA"}) == {
            "id": UUID("2D2C131C-E2A2-4DEA-887A-A7A6678B71AA")
        }

    def test_matches_list_ordered(self, data):
        assert data == {
            "3": ["index0", "index1", "index2"],
            ...: ...,
        }
        assert data == {
            "4": [
                {"id": 1, ...: ...},
                {"id": 2, ...: ...},
                {"id": 3, ...: ...},
            ],
            ...: ...,
        }

    def test_matches_list_unordered(self, data):
        assert data == {
            "3": [..., "index2"],
            ...: ...,
        }
        assert data == {
            "3": [..., "index2", "index1", "index0"],
            ...: ...,
        }
        assert data == {
            "4": [
                ...,
                {"name": "baz", ...: ...},
            ],
            ...: ...,
        }

    def test_keys_do_not_match(self, data):
        with pytest.raises(MatcherKeysDoNotMatch) as e:
            assert data == {"1": ..., "2": ..., "3": ..., "5": ...}
        assert e.value.args == ("", ("1", "2", "3", "4"), ("1", "2", "3", "5"))

        with pytest.raises(MatcherKeysDoNotMatch) as e:
            assert data == {"2": {"a": ..., "b": ..., "c": ...}, ...: ...}
        assert e.value.args == ("2", ("a", "b"), ("a", "b", "c"))

    def test_missing_required_key(self, data):
        with pytest.raises(MatcherMissingRequiredKey) as e:
            assert data == {"foo": ..., ...: ...}
        assert e.value.args == ("foo",)

        with pytest.raises(MatcherMissingRequiredKey) as e:
            assert data == {"2": {"foo": ..., ...: ...}, ...: ...}
        assert e.value.args == ("2.foo",)

    def test_regex_mismatch(self, data):
        pattern = re.compile("xyz")

        with pytest.raises(MatcherRegexMismatch) as e:
            assert data == {"1": pattern, ...: ...}
        assert e.value.args == ("1", pattern, "one")

    def test_value_mismatch(self, data):
        with pytest.raises(MatcherValueMismatch) as e:
            assert data == {"1": "ONE", ...: ...}
        assert e.value.args == ("1", "ONE", "one")

        with pytest.raises(MatcherValueMismatch) as e:
            assert data == {"2": {"a": "ayy!", ...: ...}, ...: ...}
        assert e.value.args == ("2.a", "ayy!", "A")

        with pytest.raises(MatcherValueMismatch) as e:
            assert data == {"3": ["index0", "index1", "ayy!"], ...: ...}
        assert e.value.args == ("3.2", "ayy!", "index2")

    def test_length_too_short(self, data):
        with pytest.raises(MatcherLengthTooShort) as e:
            assert data == {"3": ["a", "b"], ...: ...}
        assert e.value.args == ("3", ["a", "b"], ["index0", "index1", "index2"])

    def test_length_too_long(self, data):
        with pytest.raises(MatcherLengthTooLong) as e:
            assert data == {"3": ["a", "b", "c", "d"], ...: ...}
        assert e.value.args == ("3", ["a", "b", "c", "d"], ["index0", "index1", "index2"])

    def test_no_match_found(self, data):
        with pytest.raises(MatcherNoMatchFound) as e:
            assert data == {"3": ["index4", ...], ...: ...}
        assert e.value.args == ("3", "index4", ["index0", "index1", "index2"])

        with pytest.raises(MatcherNoMatchFound) as e:
            assert data == {"3": ["index2", "index4", ...], ...: ...}
        assert e.value.args == ("3", "index4", ["index0", "index1"])

    def test_none_match(self):
        assert DeepDict({"abc": None}) == {"abc": None}

    def test_none_mismatch(self):
        with pytest.raises(MatcherTypeMismatch) as e:
            assert DeepDict({"abc": "not None"}) == {"abc": None}
        assert e.value.args == ("abc", None, "not None")

    def test_datetime_match(self):
        assert DeepDict({"created": "2024-01-11T11:11:11-08:00"}) == {"created": arrow.get("2024-01-11T13:11:11-06:00")}
        assert DeepDict({"created": "2024-01-11T11:11:11Z"}) == {"created": datetime.datetime(2024, 1, 11, 11, 11, 11)}

    def test_datetime_mismatch(self):
        with pytest.raises(MatcherDatetimeMismatch) as e:
            assert DeepDict({"created": "2024-01-11T11:11:11-08:00"}) == {"created": arrow.get("2025-01-13T13:13:13Z")}
        assert e.value.args == ("created", arrow.get("2025-01-13T13:13:13Z"), "2024-01-11T11:11:11-08:00")

        with pytest.raises(MatcherTypeMismatch) as e:
            assert DeepDict({"created": "yesterday"}) == {"created": arrow.get("2024-01-11T13:11:11-06:00")}
        assert e.value.args == ("created", arrow.get("2024-01-11T13:11:11-06:00"), "yesterday")
        assert isinstance(e.value.__cause__, arrow.ParserError)

    def test_decimal_match(self):
        assert DeepDict({"amount": "0"}) == {"amount": Decimal("0.00")}
        assert DeepDict({"amount": "0.00"}) == {"amount": Decimal("0")}

    def test_decimal_mismatch(self):
        with pytest.raises(MatcherValueMismatch) as e:
            assert DeepDict({"amount": "123.45"}) == {"amount": Decimal("234.56")}
        assert e.value.args == ("amount", Decimal("234.56"), Decimal("123.45"))

        with pytest.raises(MatcherTypeMismatch) as e:
            assert DeepDict({"amount": "not a number"}) == {"amount": Decimal("234.56")}
        assert e.value.args == ("amount", Decimal("234.56"), "not a number")
        assert isinstance(e.value.__cause__, decimal.DecimalException)

        with pytest.raises(MatcherTypeMismatch) as e:
            assert DeepDict({"amount": None}) == {"amount": Decimal("234.56")}
        assert e.value.args == ("amount", Decimal("234.56"), None)
        assert isinstance(e.value.__cause__, TypeError)

    def test_readme_example(self, raw_data):
        assert DeepDict(raw_data) == {
            "1": ...,  # [1]
            "3": ["index1", ...],  # [3]
            "4": [
                {
                    "name": re.compile("ba."),
                    ...: ...,
                },
                ...,
            ],  # [4]
            ...: ...,  # [2]
        }
