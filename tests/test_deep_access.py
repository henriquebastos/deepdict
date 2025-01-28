# Pip imports
from unittest import mock

import pytest

# Internal imports
from dictdeeper import DeepDictIndexError, DeepDictKeyError, DeepDictValueError
from dictdeeper.core import DeepDict, DeepList


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
        "4": [
            {"id": 1, "name": "foo", "shapes": ["square", "circle"]},
            {"id": 2, "name": "bar", "shapes": ["circle", "triangle"]},
            {"id": 3, "name": "baz", "shapes": ["triangle", "square"]},
        ],
    }


class TestDeepAccess:
    @pytest.fixture
    def data(self, raw_data):
        return DeepDict(raw_data)

    def test_shallow_contains(self, data):
        assert "1" in data
        assert "5" not in data
        assert "index0" in data["3"]
        assert "index123" not in data["3"]

    def test_deep_contains(self, data):
        assert "1.a" not in data
        assert "2.a" in data
        assert "2.b.ii" in data
        assert "3.1" in data

    def test_shallow_getitem(self, data):
        assert data["1"] == "one"
        assert data["2"]["b"]["ii"] == "II"
        assert isinstance(data["2"], DeepDict)
        assert isinstance(data["3"], DeepList)
        with pytest.raises(KeyError):
            _ = data["5"]

    def test_convert_to_list(self, data):
        assert list(data["3"]) == ["index0", "index1", "index2"]
        assert [type(x) for x in list(data["4"])] == [dict, dict, dict]

    def test_deep_getitem(self, data):
        assert data["2.a"] == "A"
        assert data["2.b.ii"] == "II"
        assert data["2"]["b.ii"] == "II"
        assert data["3.0"] == "index0"
        assert data["3.1"] == "index1"
        assert data["3"][0] == "index0"
        assert data["3"]["0"] == "index0"
        assert data["4.0.id"] == 1
        assert data["4.1.shapes.1"] == "triangle"
        assert data["4.1"]["shapes"] == ["circle", "triangle"]
        assert data["4"]["1.shapes"] == ["circle", "triangle"]

        list_of_lists = DeepList(["turtles", ["turtles", ["turtles"]]])
        assert list_of_lists["1.1"] == ["turtles"]
        assert list_of_lists["1.1.0"] == "turtles"

    def test_deep_getitem_key_error(self, data):
        with pytest.raises(DeepDictKeyError) as e:
            _ = data["2.b.iii.x.y.z"]
        assert repr(e.value.args) == "(Key(origin='2.b', part='iii'),)"

        with pytest.raises(DeepDictKeyError) as e:
            _ = data["2.c"]
        assert repr(e.value.args) == "(Key(origin='2', part='c'),)"

    def test_deep_getitem_index_error(self, data):
        with pytest.raises(DeepDictIndexError) as e:
            _ = data["3.3"]
        assert repr(e.value.args) == "(Key(origin='3', part='3'),)"

    def test_deep_getitem_value_error(self, data):
        with pytest.raises(DeepDictValueError) as e:
            _ = data["2.b.ii.foo.bar"]
        assert repr(e.value.args) == "(Key(origin='2.b.ii', part='foo'),)"

    def test_shallow_get(self, data):
        assert data.get("1") == "one"
        assert isinstance(data.get("2"), DeepDict)
        assert isinstance(data.get("3"), DeepList)
        assert data.get("5", mock.sentinel.DEFAULT) is mock.sentinel.DEFAULT

    def test_deep_get(self, data):
        assert data.get("2.a") == "A"
        assert data.get("2.b.ii") == "II"
        assert data.get("3.0") == "index0"
        assert data.get("3.1") == "index1"
        assert data.get("2.b.iii.x.y.z", mock.sentinel.DEFAULT) is mock.sentinel.DEFAULT
        assert data.get("2.c", mock.sentinel.DEFAULT) is mock.sentinel.DEFAULT
        assert data.get("3.3", mock.sentinel.DEFAULT) is mock.sentinel.DEFAULT

    def test_nested(self, data):
        d = data["2"]
        assert isinstance(d, DeepDict)
        assert d["b.ii"] == "II"

    def test_dict_items(self, data):
        item_types = {key: type(value) for key, value in data.items()}
        assert item_types == {
            "1": str,
            "2": DeepDict,
            "3": DeepList,
            "4": DeepList,
        }

    def test_dict_values(self, data):
        item_types = [type(value) for value in data.values()]
        assert item_types == [str, DeepDict, DeepList, DeepList]

    def test_dict_len(self, data):
        assert len(data) == 4

    def test_list_len(self, data):
        assert len(data["3"]) == 3

    def test_repr(self):
        assert repr(DeepDict({"a": "b"})) == "DeepDict({'a': 'b'})"
        assert repr(DeepList([1, 2, 3])) == "DeepList([1, 2, 3])"

    def test_keys(self, data):
        assert list(data.keys()) == ["1", "2", "3", "4"]
