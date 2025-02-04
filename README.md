# DictDeeper: The easy way to manipulate deeply-nested dicts like JSON-style objects.

## What you can do with DictDeeper?

1. You can navigate to any depth with a simple dotted-string key notation.
2. You can even transparently navigate within lists inside dicts.
3. You can do full and partial validate of your dict structure in a declarative way.
4. You can do full and partial value comparison in a declarative way.
5. You can arrange a variety of strategies to merge dicts into a single one.

## How to use it?

To access values nested in an object using a dotted-key notation,
wrap the object using `DeepDict`, then use the standard `dict` interface:

```python
from dictdeeper import DeepDict


request_body = DeepDict(request.json())
is_scheduled = request_body.get("data.attributes.date_scheduled") is not None
```

## How to match the structure of a deeply nested dict?

Use DeepDict to compare the values within a `dict` or `list` against a partial specification.

Both `DeepDict` and `DeepList` objects automatically use deep matching in their `__eq__` method.

When a comparison fails, a `MatcherError` is raised, with the location and context of the mismatch.

Here are the things you can use in the matching spec:

1. **`some_key` in a `dict` exists of any value**: Include `"some_key": ...` in the spec.
2. **Other keys may exist in a `dict`**: Include `...: ...` in the spec.
3. **Matching items in an unordered `list`**: Include `...` as an item in the spec.
4. **Matching a string against a regex**: Use `re.compile("your-regex-here")` as a value in the spec.

Example:

```python
data = {
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

assert DeepDict(data) == {
    "1": ...,  # [1]
    "3": ["index1", ...],  # [3]
    "4": [{"name": re.compile("ba."), ...: ...,}, ...],  # [4]
    ...: ...,  # [2]
}
```

## Thank you to Routable

[Routable](https://routable.com) sponsored the development of this library.
Working at [Routable](https://routable.com) is an awesome experience, with a developer-first culture that fosters innovation and growth.
If you're interested in joining a dynamic team, [check out our job opportunities here](https://routable.com/careers/)!

## Authors

- Henrique Bastos <henrique@bastos.net>
- Matthew Scott <matt@11craft.com>
