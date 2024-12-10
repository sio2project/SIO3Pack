from enum import Enum


class ModelSolutionKind(Enum):
    NORMAL = ""
    SLOW = "s"
    INCORRECT = "b"

    @classmethod
    def from_regex(cls, group):
        if group == "":
            return cls.NORMAL
        if group == "s":
            return cls.SLOW
        if group == "b":
            return cls.INCORRECT
        raise ValueError(f"Invalid model solution kind: {group}")

    @classmethod
    def all(cls):
        return [cls.NORMAL, cls.SLOW, cls.INCORRECT]

    @classmethod
    def django_choices(cls):
        return [(kind.value, kind.name) for kind in cls.all()]
