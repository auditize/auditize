import re

# We used to use callee (https://github.com/Xion/callee), however the project is unfortunatelly no longer maintained,
# so we implemnented our own matchers (the subset we actually use) while keeping the same API.


class IsA:
    def __init__(self, type):
        self.type = type

    def __eq__(self, other):
        return isinstance(other, self.type)

    def __repr__(self):
        return f"IsA({self.type})"


class String(IsA):
    def __init__(self):
        super().__init__(str)


class Contains:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, str) and self.value in other

    def __repr__(self):
        return f"Contains({self.value})"


class StartsWith:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, str) and other.startswith(self.value)

    def __repr__(self):
        return f"StartsWith({self.value})"


class Regex:
    def __init__(self, pattern):
        self.pattern = pattern

    def __eq__(self, other):
        return isinstance(other, str) and re.match(self.pattern, other)

    def __repr__(self):
        return f"Regex({self.pattern})"


class Eq:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return other == self.value

    def __repr__(self):
        return f"Eq({self.value})"


class OneOf:
    def __init__(self, values):
        self.values = values

    def __eq__(self, other):
        return any(other == value for value in self.values)

    def __repr__(self):
        return f"OneOf({self.values})"
