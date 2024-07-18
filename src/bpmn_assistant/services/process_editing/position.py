from typing import Optional


class Position:
    def __init__(self, index: int, path: Optional[list] = None):
        self.index = index
        self.path = path or []

    def __repr__(self):
        return f"Position(index={self.index}, path={self.path})"

    @classmethod
    def from_dict(cls, position_dict: dict):
        return cls(position_dict["index"], position_dict.get("path"))

    def to_dict(self):
        return {"index": self.index, "path": self.path}

    def is_top_level(self):
        return len(self.path) == 0
