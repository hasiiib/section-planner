from dataclasses import dataclass, asdict

DAYS = ('Sat','Sun','Mon','Tue','Wed','Thu','Fri')

@dataclass(frozen=True)
class Meeting:
    day: str
    start: int
    end: int
    room: str = ''

@dataclass(frozen=True)
class Section:
    program: str
    code: str
    title: str
    section: str
    faculty: str
    initial: str
    credit: str
    meetings: tuple[Meeting, ...]
    serial: int = 0
    notes: str = ''
    uncertain: tuple[str, ...] = ()

    @property
    def key(self):
        return (self.program, self.code, self.section)

    def to_dict(self):
        x=asdict(self)
        return x

    @classmethod
    def from_dict(cls, d):
        d=dict(d)
        d['meetings']=tuple(Meeting(**m) for m in d['meetings'])
        d['uncertain']=tuple(d.get('uncertain',()))
        return cls(**d)
