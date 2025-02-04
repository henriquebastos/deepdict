from __future__ import annotations

import decimal
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Mapping
from unittest.mock import sentinel
from uuid import UUID

import arrow

from dictdeeper.exceptions import (
    MatcherDatetimeMismatch,
    MatcherError,
    MatcherKeysDoNotMatch,
    MatcherLengthTooLong,
    MatcherLengthTooShort,
    MatcherMissingRequiredKey,
    MatcherNoMatchFound,
    MatcherRegexMismatch,
    MatcherTypeMismatch,
    MatcherValueMismatch,
)


class Matcher(ABC):
    def __init__(self, wrapped_obj):
        self.wrapped_obj = wrapped_obj

    def __eq__(self, spec):
        return self.matches(spec)

    @staticmethod
    def wrap_value(value, spec):
        if spec is ...:
            return value
        if isinstance(value, Mapping):
            return DictMatcher(value)
        if isinstance(value, (list, tuple)):
            return ListMatcher(value)
        return value

    @staticmethod
    def validate_match(value, spec, key_location):
        # Ellipsis: Always match.
        if spec is ...:
            return True

        # None: Raise error if not None.
        if spec is None and value is not None:
            raise MatcherTypeMismatch(key_location, spec, value)

        # Dict: Recursively match.
        if isinstance(value, DictMatcher) and isinstance(spec, Mapping):
            return value.matches(spec, location=key_location)

        # List: Recursively match.
        if isinstance(value, ListMatcher) and isinstance(spec, (list, tuple)):
            return value.matches(spec, location=key_location)

        # Regex: Match value with spec.
        if isinstance(spec, re.Pattern):
            if not spec.match(value):
                raise MatcherRegexMismatch(key_location, spec, value)
            return True

        # Datetime: Normalize and compare.
        if isinstance(spec, (arrow.Arrow, datetime)):
            try:
                if arrow.get(value) != arrow.get(spec):
                    raise MatcherDatetimeMismatch(key_location, spec, value)
            except arrow.ParserError as e:
                raise MatcherTypeMismatch(key_location, spec, value) from e
            return True

        # UUID: Normalize for later comparison.
        if isinstance(spec, UUID):
            value = str(value).lower()
            spec = str(spec)

        # Decimal: Normalize for later comparison.
        if isinstance(spec, decimal.Decimal):
            try:
                value = decimal.Decimal(value)
            except Exception as e:
                raise MatcherTypeMismatch(key_location, spec, value) from e

        # Final comparison.
        if value != spec:
            raise MatcherValueMismatch(key_location, spec, value)

        return True

    @abstractmethod
    def matches(self, spec, location=""):
        """Deeply compare `self.wrapped_obj` with `spec`, including `location` with any `MatcherError` raised."""


class DictMatcher(Matcher):
    wrapped_obj: dict

    def get_wrapped(self, key, spec, default=None):
        try:
            value = self.wrapped_obj[key]
        except KeyError:
            return default
        return self.wrap_value(value, spec)

    def matches(self, spec: Mapping, location=""):
        if set(self.wrapped_obj) != set(spec) and ... not in spec:
            raise MatcherKeysDoNotMatch(location, tuple(self.wrapped_obj), tuple(spec))
        for key in spec:
            key_location = f"{location}.{key}" if location else str(key)
            subspec = spec[key]
            wrapped_value = self.get_wrapped(key, subspec, sentinel.DOES_NOT_EXIST)
            if key is ...:
                continue
            if subspec is ... and wrapped_value is sentinel.DOES_NOT_EXIST:
                raise MatcherMissingRequiredKey(key_location)
            self.validate_match(wrapped_value, subspec, key_location)
        return True


class ListMatcher(Matcher):
    wrapped_obj: list

    def matches(self, spec: list, location=""):
        if isinstance(spec, list) and ... in spec:
            return self._matches_unordered(spec, location)
        else:
            return self._matches_ordered(spec, location)

    def _matches_ordered(self, spec: list, location=""):
        if len(spec) < len(self.wrapped_obj):
            raise MatcherLengthTooShort(location, spec, self.wrapped_obj)
        if len(spec) > len(self.wrapped_obj):
            raise MatcherLengthTooLong(location, spec, self.wrapped_obj)
        for index, (value, subspec) in enumerate(zip(self.wrapped_obj, spec)):
            key_location = f"{location}.{index}" if location else str(index)
            wrapped_value = self.wrap_value(value, subspec)
            self.validate_match(wrapped_value, subspec, key_location)
        return True

    def _matches_unordered(self, spec: list, location=""):
        values = self.wrapped_obj.copy()
        for subspec in spec:
            if subspec is ...:
                continue
            for index, value in enumerate(values):
                if value is sentinel.MATCH_FOUND:
                    continue
                value = self.wrap_value(value, subspec)
                try:
                    self.validate_match(value, subspec, location)
                except MatcherError:
                    continue
                else:
                    values[index] = sentinel.MATCH_FOUND
                    break
            else:
                remaining_values = [value for value in values if value is not sentinel.MATCH_FOUND]
                raise MatcherNoMatchFound(location, subspec, remaining_values)
        return True
