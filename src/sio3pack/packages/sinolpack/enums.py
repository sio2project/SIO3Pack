from enum import Enum


class ModelSolutionKind(Enum):
    NORMAL = 0
    SLOW = 1
    INCORRECT = 2

    @classmethod
    def from_regex(cls, group):
        if group == '':
            return cls.NORMAL
        if group == 's':
            return cls.SLOW
        if group == 'b':
            return cls.INCORRECT
        raise ValueError(f"Invalid model solution kind: {group}")
