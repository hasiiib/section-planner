"""Position-aware extraction of UIU's landscape, text-based course-offering tables.
Never infer missing teaching times, days, or section identities.
"""
import re
from datetime import datetime
import fitz
from .model import Section, Meeting, DAYS

TIME_RE=re.compile(r'\d{1,2}:\d{2}:?(?:AM|PM)\s*-\s*\d{1,2}:\d{2}:?(?:AM|PM)',re.I)
DAY_RE=re.compile(r'\b(?:Sat|Sun|Mon|Tue|Wed|Thu|Fri)\b')
CODE_RE=re.compile(r'^([A-Za-z]+)\s*(\d+[A-Za-z]?)$')


def minutes(s):
    s=s.strip().upper()
    match=re.fullmatch(r'(\d{1,2}):(\d{2}):?(AM|PM)',s)
    if not match:raise ValueError(f'Invalid time: {s}')
    h,m=int(match[1]),int(match[2])
    if not 1<=h<=12 or m>59:raise ValueError(s)
    return ((h%12)+(12 if match[3]=='PM' else 0))*60+m


def time_range(s):
    m=TIME_RE.fullmatch(s.strip())
    if not m:raise ValueError(f'Invalid time interval {s!r}')
    a,b=re.split(r'\s*-\s*',s)
    start,end=minutes(a),minutes(b)
    if end<=start:raise ValueError(s)
    return start,end

# Physical text-column boundaries, measured from the source PDF's embedded glyphs.
# Room descriptions may span room1 + room2; weekdays anchor the end of room text.
EDGES=(0,33,71,122,277,323,399,423,450,536,621,716,750,792)
FIELDS=('serial','program','code','title','section','rooms','day1','day2','time1','time2','faculty','initial','credit')

def _joined(words):
    return ' '.join(w[4] for w in sorted(words,key=lambda w:(round(w[1]/3),w[0]))).strip()

def _cell(words,lo,hi):
    return _joined([w for w in words if lo<=w[0]<hi])

def parse_pdf(path):
    doc=fitz.open(path)
    result=[];warnings=[];seen=set()
    for index,page in enumerate(doc):
        ws=page.get_text('words',sort=False)
        anchors=sorted((w for w in ws if w[0]<33 and w[1]>95 and w[1]<550 and w[4].isdigit()),key=lambda w:w[1])
        for j,anchor in enumerate(anchors):
            top=anchor[1]-2
            bottom=(anchors[j+1][1]-1 if j+1<len(anchors) else 558)
            words=[w for w in ws if top<=w[1]<bottom and w[0]<790]
            cells={name:_cell(words,EDGES[k],EDGES[k+1]) for k,name in enumerate(FIELDS)}
            serial=int(anchor[4]);program=cells['program'].strip().upper()
            code=' '.join(cells['code'].split())
            problems=[]
            if program not in ('BSCSE','BSDS'):problems.append('Unrecognized program')
            if not CODE_RE.fullmatch(code):problems.append('Unrecognized course code')
            title=cells['title'];rawsection=cells['section']
            secmatch=re.match(r'^([A-Za-z]{1,3})(.*)$',rawsection)
            section=secmatch[1] if secmatch else rawsection
            if not section and title:
                # The source sometimes glues the section directly to the truncated title.
                suffix=re.search(r'([A-Z]{1,2})$',title)
                if suffix:
                    section=suffix[1] if program=='BSDS' else suffix[1][-1]
                    title=title[:-len(section)].rstrip()
            notes=secmatch[2].strip() if secmatch else ''
            if re.search(r'if\s+requir',notes,re.I):notes='(If Required)' # source cell clips the marker
            if not section:problems.append('Missing section')
            # Some room labels straddle the nominal column boundary.
            # Collect the room text but keep the two meetings separately.
            roomwords=[w for w in words if 323<=w[0]<399]
            roomtext=_joined(roomwords)
            if '(Computer Lab)' in roomtext or '(Digital Lab)' in roomtext or '(Circuit Lab)' in roomtext:
                rooms=[roomtext,'']
            else:
                rooms=[_cell(words,323,363),_cell(words,363,399)]
            days=[cells['day1'],cells['day2']]
            times=[cells['time1'],cells['time2']]
            meetings=[]
            for k,(day,t) in enumerate(zip(days,times)):
                daymatch=DAY_RE.search(day)
                if not daymatch and k==0:
                    # In two PDF rows, embedded text joins '(Com' and 'Wed'.
                    # Recover only an explicitly printed weekday token.
                    daymatch=DAY_RE.search(_cell(words,365,450))
                    if not daymatch:
                        embedded=re.search(r'(Sat|Sun|Mon|Tue|Wed|Thu|Fri)$',_cell(words,365,450))
                        daymatch=embedded
                if daymatch:
                    try:
                        start,end=time_range(t)
                        meetings.append(Meeting(daymatch.group(),start,end,rooms[k]))
                    except ValueError:problems.append(f'Invalid Time{k+1}: {t}')
                elif t and TIME_RE.search(t):problems.append(f'Time{k+1} lacks weekday')
            if not meetings:problems.append('Missing meeting schedule')
            faculty=cells['faculty']
            initial=cells['initial']
            credit=cells['credit']
            if not credit or not re.search(r'\d',credit):problems.append('Credit not verified')
            # Faculty initials are optional; TBA is a valid published value.
            if not faculty and re.search(r'if\s+requir',notes+' '+rawsection,re.I):faculty='TBA'
            # Some rows place the section and beginning of the room against each other.
            if not title:problems.append('Title missing')
            if re.search(r'\b(?:Labora|Laborator|Sci)$', title):
                problems.append('Course title is cut off in the source PDF')
            item=Section(program,code,title,section,faculty,initial,credit,tuple(meetings),serial,notes,tuple(problems))
            if item.key in seen:
                warnings.append(f'Page {index+1}, row {serial}: duplicate {item.key} (omitted)')
                continue
            seen.add(item.key)
            result.append(item)
            if problems:warnings.append(f'Page {index+1}, row {serial}, {code} {section}: {", ".join(problems)}')
    # Repair clipped titles ONLY from a demonstrably longer title printed elsewhere
    # for the exact same program + course code. Keep uncertain titles when no such
    # verified source exists; never guess words absent from the offering.
    from dataclasses import replace
    titles={}
    for section in result:
        key=(section.program,section.code)
        title=section.title.strip()
        if not any('Course title is cut off' in x for x in section.uncertain):
            if len(title)>len(titles.get(key,'')):titles[key]=title
    fixed=[];warnings=[]
    for section in result:
        key=(section.program,section.code);good=titles.get(key,'')
        clipped=any('Course title is cut off' in x for x in section.uncertain)
        if clipped and good and (good.lower().startswith(section.title.lower()) or section.title.lower().startswith(good[:max(6,len(section.title)-2)].lower())):
            section=replace(section,title=good,uncertain=tuple(x for x in section.uncertain if 'Course title is cut off' not in x))
        fixed.append(section)
        if section.uncertain:
            descriptions={
                'Course title is cut off in the source PDF': 'The course title is partially hidden in the PDF. Please check the original.',
                'Credit not verified': 'The credit value could not be read.',
                'Title missing': 'The course title is missing.',
                'Missing section': 'The section name could not be read.',
                'Missing meeting schedule': 'No complete class day and time could be found.',
            }
            detail='; '.join(descriptions.get(x,x.replace('Invalid Time','Class time could not be read:')) for x in section.uncertain)
            warnings.append(f'Page {max(1,(section.serial-1)//30+1)}, record {section.serial}, {section.code} ({section.section}): {detail}')
    return fixed,warnings,len(doc)


def detect_trimester(path):
    """Read the actual offering heading; return None when absent/ambiguous."""
    with fitz.open(path) as doc:
        for page in list(doc)[:min(3,len(doc))]:
            text=page.get_text()
            match=re.search(r'Course\s+Offerings\s*:\s*([A-Za-z]+\s+20\d{2})\s+Trimester',text,re.I)
            if match:return ' '.join(match.group(1).split()).title()
    return None
