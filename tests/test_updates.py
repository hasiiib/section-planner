from pathlib import Path
from uiu.parser import detect_trimester,parse_pdf
from uiu.scheduler import enumerate_routines
from uiu.model import Section,Meeting

PDF=Path(__file__).resolve().parents[1]/'Fall_2026_offerings.pdf'

def test_trimester_from_actual_heading():
    assert detect_trimester(PDF)=='Fall 2026'

def test_missing_faculty_initial_not_a_warning():
    sections,warnings,_=parse_pdf(PDF)
    assert len(sections)==791
    assert not any('faculty initial missing' in msg.lower() for msg in warnings)
    assert any(s.faculty=='TBA' for s in sections)

def test_one_day_with_no_second_day_is_valid():
    records,_,_=parse_pdf(PDF)
    one_day=next(s for s in records if s.serial==31)
    assert len(one_day.meetings)==1
    out=[]
    valid,rejected,complete=enumerate_routines([[one_day]],out.append)
    assert (valid,rejected,complete)==(1,0,True)

def test_generation_progress_reaches_total():
    def make(code,section,day):
        return Section('BSCSE',code,code,section,'TBA','','3',(Meeting(day,540,590,''),))
    progress=[];routines=[]
    a=[make('A','1','Sat'),make('A','2','Sun')]
    b=[make('B','1','Mon')]
    stats=enumerate_routines([a,b],routines.append,on_progress=lambda done,total:progress.append((done,total)))
    assert stats==(2,0,True)
    assert progress==[(1,2),(2,2)]
