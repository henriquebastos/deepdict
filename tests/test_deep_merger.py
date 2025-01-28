# Pip imports
import pytest

# Internal imports
from dictdeeper.merger import (
    CombineLists,
    DeepMerger,
    MergeDicts,
    MergeListOfDictsByPosition,
    MergeListsOfDictsByKey,
    Strategy,
)


class TestDeepMerge:
    @pytest.fixture(scope="class")
    def merger(self):
        return DeepMerger(
            strategies=[
                MergeListsOfDictsByKey(key=lambda idx, d: d["id"], condition=lambda d: "id" in d),
                MergeListOfDictsByPosition(),
                CombineLists(),
                MergeDicts(),
            ]
        )

    def test_merge_all_combined(self, merger):
        a = {"1": "one", "2": {"a": "A"}, "3": ["i0"], "4": [{"id": 1, "a": "i"}, {"id": 2, "a": "i"}]}

        b = {"1": "ONE", "2": {"a": "B"}, "3": ["i1"], "4": [{"id": 1, "a": "ii", "b": "ii"}, {"id": 2, "b": "ii"}]}

        assert merger(a, b) == {
            "1": "ONE",
            "2": {"a": "B"},
            "3": ["i0", "i1"],
            "4": [{"id": 1, "a": "ii", "b": "ii"}, {"id": 2, "a": "i", "b": "ii"}],
        }

    def test_default_behavior(self):
        merger = DeepMerger()
        a = {"1": "one", "2": {"a": "A"}, "3": {"id": 1, "a": "i"}, "4": {"id": 2, "a": "i"}}
        b = {"1": "ONE", "2": {"a": "B"}, "3": {"id": 1, "a": "ii", "b": "ii"}, "4": {"id": 2, "b": "ii"}}

        assert merger(a, b) == {
            "1": "ONE",
            "2": {"a": "B"},
            "3": {"id": 1, "a": "ii", "b": "ii"},
            "4": {"id": 2, "a": "i", "b": "ii"},
        }


class TestStrategy:
    def test_test_raises(self):
        with pytest.raises(NotImplementedError):
            Strategy().test({}, {})

    def test_call_raises(self):
        with pytest.raises(NotImplementedError):
            Strategy()({}, {}, None)


class TestMergeListOfDictsByPosition:
    @pytest.fixture(scope="class")
    def merger(self):
        return DeepMerger(strategies=[MergeListOfDictsByPosition()])

    def test_merge_same_position_in_list(self, merger):
        a = {1: [{"a": "i"}, {"b": "ii"}, {"e": 42}]}
        b = {1: [{"c": 1}, {"d": 2}, {"f": 51}]}
        expected = {1: [{"a": "i", "c": 1}, {"b": "ii", "d": 2}, {"e": 42, "f": 51}]}
        assert merger(a, b) == expected

    def test_merge_lists_with_different_sizes(self, merger):
        a = {1: [{"a": "i"}, {"b": "ii"}, {"e": 42}]}
        b = {1: [{"c": 1}, {"d": 2}]}
        assert merger(a, b) == merger(b, a) == {1: [{"a": "i", "c": 1}, {"b": "ii", "d": 2}, {"e": 42}]}


class TestMergeListsOfDictsWithStrategy:
    @pytest.fixture(scope="class")
    def merger(self):
        return DeepMerger([MergeListsOfDictsByKey(key=lambda idx, d: d["id"], condition=lambda d: "id" in d)])

    def test_merge_id_list_with_empty(self, merger):
        assert merger({"1": [{"id": 1, "a": "i"}]}, {"1": []}) == {"1": [{"id": 1, "a": "i"}]}

    def test_merge_empty_with_id_list(self, merger):
        assert merger({"1": []}, {"1": [{"id": 1, "a": "i"}]}) == {"1": [{"id": 1, "a": "i"}]}

    def test_merge_different_id_lists(self, merger):
        assert merger({1: [{"id": 1, "a": "i"}]}, {1: [{"id": 2, "b": "ii"}]}) == {
            1: [{"id": 1, "a": "i"}, {"id": 2, "b": "ii"}]
        }

    def test_merge_same_id_update_value(self, merger):
        assert merger({1: [{"id": 1, "a": "i"}]}, {1: [{"id": 1, "a": "ii"}]}) == {1: [{"id": 1, "a": "ii"}]}

    def test_merge_same_id_add_key(self, merger):
        assert merger({1: [{"id": 1, "a": "i"}]}, {1: [{"id": 1, "b": "ii"}]}) == {1: [{"id": 1, "a": "i", "b": "ii"}]}


class TestCombineLists:
    @pytest.fixture(scope="class")
    def merger(self):
        return DeepMerger([CombineLists()])

    def test_merge_list_with_empty(self, merger):
        assert merger({"3": ["i0"]}, {"3": []}) == {"3": ["i0"]}

    def test_merge_empty_with_list(self, merger):
        assert merger({"3": []}, {"3": ["i0"]}) == {"3": ["i0"]}

    def test_merge_lists(self, merger):
        assert merger({"3": ["i0"]}, {"3": ["i1"]}) == {"3": ["i0", "i1"]}


class TestMergeDicts:
    @pytest.fixture(scope="class")
    def merger(self):
        return DeepMerger([MergeDicts()])

    def test_merge_empty_with_one(self, merger):
        assert merger({"1": "one"}, {}) == {"1": "one"}

    def test_merge_one_with_empty(self, merger):
        assert merger({}, {"1": "one"}) == {"1": "one"}

    def test_merge_b_override_a(self, merger):
        assert merger({"1": "one"}, {"1": "ONE"}) == {"1": "ONE"}

    def test_merge_nested_empty_with_value(self, merger):
        assert merger({"2": {"a": "A"}}, {"2": {}}) == {"2": {"a": "A"}}

    def test_merge_empty_nested_with_value(self, merger):
        assert merger({"2": {}}, {"2": {"a": "A"}}) == {"2": {"a": "A"}}

    def test_merge_nested_values(self, merger):
        assert merger({"2": {"a": "A"}}, {"2": {"a": "B"}}) == {"2": {"a": "B"}}
