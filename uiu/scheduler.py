from dataclasses import dataclass
from .model import Section

@dataclass(frozen=True)
class Conflict:
    left: Section
    right: Section
    day: str
    start: int
    end: int


def conflicts(a: Section, b: Section):
    return [Conflict(a,b,x.day,max(x.start,y.start),min(x.end,y.end))
            for x in a.meetings for y in b.meetings
            if x.day==y.day and max(x.start,y.start)<min(x.end,y.end)]


def verify(routine):
    seen=set()
    issues=[]
    for i,a in enumerate(routine):
        identity=(a.program,a.code)
        if identity in seen:
            issues.append(f'Duplicate course {a.code}')
        seen.add(identity)
        if not a.meetings or any(m.end<=m.start for m in a.meetings) or any('time' in note.lower() or 'weekday' in note.lower() or 'meeting' in note.lower() for note in a.uncertain):
            issues.append(f'Unverified schedule for {a.code} {a.section}')
        for b in routine[:i]:
            issues.extend(conflicts(a,b))
    return issues


def enumerate_routines(groups, on_valid, on_conflict=None, cancelled=lambda:False, progress=None, on_progress=None):
    """Depth-first exhaustive enumeration. Returns (valid, rejected, complete)."""
    if not groups or any(not group for group in groups):
        return (0,0,True)
    codes=[(g[0].program,g[0].code) for g in groups]
    if len(set(codes))!=len(codes):
        raise ValueError('Each selected course must occur exactly once')
    valid=invalid=0
    selected=[]
    completed_roots=0
    total_roots=len({s.key for s in groups[0]})
    def dfs(depth):
        nonlocal valid,invalid,completed_roots
        if cancelled():return False
        if depth==len(groups):
            valid+=1
            on_valid(tuple(selected))
            if progress:progress(valid,invalid)
            return True
        seen=set()
        for candidate in groups[depth]:
            if cancelled():return False
            if candidate.key in seen:continue
            seen.add(candidate.key)
            if not candidate.meetings or any('time' in note.lower() or 'weekday' in note.lower() or 'meeting' in note.lower() for note in candidate.uncertain):
                invalid+=1
                if on_conflict:on_conflict(tuple(selected)+(candidate,),f'Incomplete/uncertain meeting data: {candidate.code} {candidate.section}')
                if depth==0:
                    completed_roots+=1
                    if on_progress:on_progress(completed_roots,total_roots)
                continue
            collision=next((c for prior in selected for c in conflicts(candidate,prior)),None)
            if collision:
                invalid+=1
                if on_conflict:on_conflict(tuple(selected)+(candidate,),collision)
                if depth==0:
                    completed_roots+=1
                    if on_progress:on_progress(completed_roots,total_roots)
                continue
            selected.append(candidate)
            complete=dfs(depth+1)
            selected.pop()
            if depth==0:
                completed_roots+=1
                if on_progress:on_progress(completed_roots,total_roots)
            if not complete:return False
        return True
    finished=dfs(0)
    return valid,invalid,finished


def time_label(minute):
    h,m=divmod(minute,60)
    return f'{(h-1)%12+1}:{m:02d} {"AM" if h<12 else "PM"}'


def is_conditional(section):
    """Only honor explicitly marked conditional sections, never infer from faculty."""
    return 'if required' in (section.section+' '+section.notes).lower() or 'if required' in ' '.join(section.uncertain).lower()


def generate_preferred(groups, on_valid, cancelled=lambda:False, on_progress=None):
    """Enumerate regular-only first; use conditional sections only if NO regular
    complete schedule exists. Return (valid, rejected, complete, conditional_used)."""
    if not groups or any(not g for g in groups):return (0,0,True,False)
    regular=[[s for s in g if not is_conditional(s)] for g in groups]
    if all(regular):
        count,rejected,complete=enumerate_routines(regular,on_valid,cancelled=cancelled,on_progress=on_progress)
        if not complete or count:return (count,rejected,complete,False)
    else:
        rejected=0
    if cancelled():return (0,rejected,False,False)
    count,bad,complete=enumerate_routines(groups,on_valid,cancelled=cancelled,on_progress=on_progress)
    return (count,rejected+bad,complete,True)
