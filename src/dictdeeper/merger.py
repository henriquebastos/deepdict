from itertools import zip_longest


class Strategy:
    def test(self, a, b):
        """
        Test if this strategy should be applied.
        """
        raise NotImplementedError("Must implement test method.")

    def __call__(self, a, b, merger):
        """
        Execute the merging strategy.
        """
        raise NotImplementedError("Must implement __call__ method.")


class MergeListOfDictsByPosition(Strategy):
    def test(self, a, b):
        return isinstance(a, list) and isinstance(b, list) and all(isinstance(item, dict) for item in a + b)

    def __call__(self, a, b, merger):
        return list(merger(i, j) for i, j in zip_longest(a, b, fillvalue={}))


class MergeListsOfDictsByKey(Strategy):
    def __init__(self, key, condition=lambda d: True):
        self.condition = condition
        self.strategy = key

    def test(self, a, b):
        return (
            isinstance(a, list)
            and isinstance(b, list)
            and all(isinstance(item, dict) and self.condition(item) for item in a + b)
        )

    def __call__(self, a, b, merger):
        temp_dict = {self.strategy(idx, item): item for idx, item in enumerate(a)}
        for idx, new_item in enumerate(b):
            item_key = self.strategy(idx, new_item)
            if item_key in temp_dict:
                temp_dict[item_key] = merger(temp_dict[item_key], new_item)
            else:
                temp_dict[item_key] = new_item
        return list(temp_dict.values())


class CombineLists(Strategy):
    def test(self, a, b):
        return isinstance(a, list) and isinstance(b, list)

    def __call__(self, a, b, merger):
        return a + b


class MergeDicts(Strategy):
    def test(self, a, b):
        return isinstance(a, dict) and isinstance(b, dict)

    def __call__(self, a, b, merger):
        return merger(a, b)


class DeepMerger:
    def __init__(self, strategies=(MergeDicts(),)):
        self.strategies = strategies

    def __call__(self, a: dict, b: dict):
        result = a.copy()
        for k, v in b.items():
            result[k] = self.merge_values(result.get(k, None), v)
        return result

    def merge_values(self, a_val, b_val):
        for strategy in self.strategies:
            if strategy.test(a_val, b_val):
                return strategy(a_val, b_val, merger=self)
        return b_val
