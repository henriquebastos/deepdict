from __future__ import annotations

from collections.abc import Mapping, Sequence

from dictdeeper.exceptions import DeepDictIndexError, DeepDictKeyError, DeepDictValueError, MatcherError
from dictdeeper.matcher import DictMatcher, ListMatcher


def DeepFactory(obj):  # noqa
    if isinstance(obj, dict):
        return DeepDict(obj)
    elif isinstance(obj, (list, tuple)):
        return DeepList(obj)
    return obj


class DeepDict(Mapping):
    def __init__(self, wrapped_obj):
        assert isinstance(wrapped_obj, dict)
        self.wrapped_obj = wrapped_obj

    def __contains__(self, key):
        try:
            _ = self[key]
            return True
        except KeyError:
            return False

    def __eq__(self, spec: Mapping):
        """Convenience method to match against a spec."""
        return DictMatcher(self.wrapped_obj).matches(spec)

    def __iter__(self):
        yield from iter(self.wrapped_obj)

    def __len__(self):
        return len(self.wrapped_obj)

    def __getitem__(self, key):
        return DeepFactory(Traversor(self.wrapped_obj)[key])

    def __repr__(self):
        return f"{self.__class__.__name__}({self.wrapped_obj!r})"

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return self.wrapped_obj.keys()

    def items(self):
        for key in self:
            yield key, self[key]

    def values(self):
        for key in self:
            yield self[key]


class DeepList(Sequence):
    def __init__(self, wrapped_obj):
        assert isinstance(wrapped_obj, (list, tuple))
        self.wrapped_obj = wrapped_obj

    def __contains__(self, item):
        try:
            return self == [item, ...]
        except MatcherError:
            return False

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.wrapped_obj[index]

        return DeepFactory(Traversor(self.wrapped_obj)[index])

    def __eq__(self, spec: list):
        """Convenience method to match against a spec."""
        return ListMatcher(self.wrapped_obj).matches(spec)

    def __len__(self):
        return len(self.wrapped_obj)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.wrapped_obj!r})"


class Key(str):
    def __new__(cls, part, origin=""):
        part = super().__new__(cls, part)
        part.origin = origin
        return part

    def __format__(self, format_spec=None):
        if format_spec != "origin":
            return self

        return self if self.origin == "" else f"{self.origin}.{self}"

    def __repr__(self):
        return f"{self.__class__.__name__}(origin={str(self.origin)!r}, part={str(self)!r})"


class NestedKey(str):
    SEP = "."

    def __new__(cls, key, origin=""):
        if not isinstance(key, str):
            raise TypeError(f"{cls.__name__} only works with str keys.")

        path = cls._path(key, origin)
        dk = super().__new__(cls, cls._collapse(path))
        dk.path = path
        return dk

    @classmethod
    def _path(cls, key, origin):
        return ([origin] if origin else []) + key.split(cls.SEP)

    @classmethod
    def _collapse(cls, path):
        return cls.SEP.join(path)

    def __repr__(self):
        return f"{self.__class__.__name__}({str(self)!r})"

    def __iter__(self):
        origin = ""
        for part in (Key(p, origin) for p in self.path):
            yield part
            origin = f"{part:origin}"


class Traversor:
    def __init__(self, wrapped_obj):
        self.wrapped_obj = wrapped_obj

    def __repr__(self):
        return f"{self.__class__.__name__}({self.wrapped_obj!r})"

    @staticmethod
    def _value_from_list(part, value):
        try:
            value = value[int(part)]
        except IndexError as e:
            raise DeepDictIndexError(part) from e
        return value

    @staticmethod
    def _value_from_dict(part, value):
        try:
            value = value[part]
        except KeyError as e:
            raise DeepDictKeyError(part) from e
        return value

    def __getitem__(self, key):
        key = NestedKey(key)
        value = self.wrapped_obj
        for part in key:
            if isinstance(value, dict):
                value = self._value_from_dict(part, value)
            elif isinstance(value, (list, tuple)):
                value = self._value_from_list(part, value)
            else:
                raise DeepDictValueError(part)

        return value
