from dataclasses import dataclass, field


@dataclass
class AuthUser:
    username: str
    email: str
    groups: list[str] = field(default_factory=list)
    sub: str = ""

    def has_group(self, group: str) -> bool:
        return group in self.groups
