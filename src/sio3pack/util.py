import re


def naturalsort_key(key):
    convert = lambda text: int(text) if text.isdigit() else text
    return [convert(c) for c in re.split("([0-9]+)", key)]
