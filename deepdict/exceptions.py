class DeepDictKeyError(KeyError):
    pass


class DeepDictValueError(KeyError):
    pass


class DeepDictIndexError(KeyError):
    pass


class MatcherError(Exception):
    pass


class MatcherKeysDoNotMatch(MatcherError):
    pass


class MatcherMissingRequiredKey(MatcherError):
    pass


class MatcherRegexMismatch(MatcherError):
    pass


class MatcherDatetimeMismatch(MatcherError):
    pass


class MatcherValueMismatch(MatcherError):
    pass


class MatcherTypeMismatch(MatcherError):
    pass


class MatcherLengthTooShort(MatcherError):
    pass


class MatcherLengthTooLong(MatcherError):
    pass


class MatcherNoMatchFound(MatcherError):
    pass
