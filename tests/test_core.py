import csv
from pathlib import Path
import pytest
from uiu.model import Meeting, Section
from uiu.parser import minutes,time_range,parse_pdf
from uiu.scheduler import enumerate_routines,verify,conflicts
from uiu.storage import Store
from uiu.exports import export

def s(code,section,meetings,program='BSCSE'):
    return Section(program,code,code,section,'Teacher','T','3',tuple(Meeting(*m) for m in meetings))

def collect(groups):
    out=[];details=[]
    result=enumerate_routines(groups,out.append,lambda a,c:details.append(c))
    return out,details,result

def test_time():
    assert minutes('12:30:PM')==750
    assert minutes('12:30:AM')==30
    assert time_range('08:30:AM - 09:50:AM')==(510,590)
    with pytest.raises(ValueError):time_range('12:30:PM - 09:50:AM')

def test_exactly_one_section_per_course():
    a=s('A','1',[('Sat',510,560,'101')]);b=s('A','2',[('Sun',510,560,'102')]);c=s('B','1',[('Mon',510,560,'103')])
    out,_,stats=collect([[a,b],[c]])
    assert len(out)==2 and stats==(2,0,True)
    assert all(len(x)==2 and len({z.code for z in x})==2 for x in out)
    with pytest.raises(ValueError):collect([[a],[b]])

def test_all_meetings_and_nonadjacent_conflict():
    a=s('A','A',[('Sat',510,590,'1'),('Tue',510,590,'1')])
    b=s('B','A',[('Sun',510,590,'1')])
    c=s('C','A',[('Tue',550,600,'1')])
    out,why,stats=collect([[a],[b],[c]])
    assert not out and why and stats[0]==0
    assert len(a.meetings)==2

def test_boundaries_days_and_no_solution():
    a=s('A','A',[('Sat',510,590,'1')]);b=s('B','A',[('Sat',590,610,'2')]);c=s('C','A',[('Sun',510,590,'3')]);d=s('D','A',[('Sat',520,600,'4')])
    assert not conflicts(a,b) and not conflicts(a,c)
    assert conflicts(a,d)
    assert collect([[a],[b],[c]])[2][0]==1
    assert collect([[a],[d]])[2][0]==0

def test_exhaustive_and_duplicate_sections():
    a=[s('A',str(i),[('Sat',600+i*100,650+i*100,'')]) for i in range(3)]
    b=[s('B',str(i),[('Sun',600+i*100,650+i*100,'')]) for i in range(4)]
    out,_,stats=collect([a+[a[0]],b])
    assert len(out)==12 and stats==(12,0,True)

def test_cancel():
    a=[s('A',str(i),[('Sat',i*100,i*100+20,'')]) for i in range(20)]
    out=[];flag=[False]
    def add(r):out.append(r);flag[0]=True
    _,_,done=enumerate_routines([a,a[:0]+[s('B','1',[('Sun',1,20,'')])]],add,cancelled=lambda:flag[0])
    assert not done and len(out)==1

def test_storage(tmp_path):
    store=Store(tmp_path/'data.sqlite3');a=s('A','1',[('Sat',510,590,'101')]);store.import_sections([a]);assert store.sections()==[a]
    rid=store.save('Test',[a]);assert store.load(rid)==[a]
    store.favorite(rid,True);assert store.list_routines()[0][3]==1
    store.delete(rid);assert store.list_routines()==[]

def test_exports(tmp_path):
    a=s('A','1',[('Sat',510,590,'101'),('Tue',510,590,'101')])
    for ext in ['csv','xlsx','pdf','png']:
        path=tmp_path/f'routine.{ext}';export([a],path)
        assert path.exists() and path.stat().st_size>30
    with (tmp_path/'routine.csv').open(encoding='utf-8-sig') as f:assert len(list(csv.reader(f)))==4

def test_pdf_real():
    pdf=Path(__file__).resolve().parents[1]/'Fall_2026_offerings.pdf'
    if not pdf.exists():pytest.skip('Bundled source PDF not present')
    data,warnings,pages=parse_pdf(pdf)
    assert pages==54
    assert len(data)==791
    assert {s.program for s in data}=={'BSCSE','BSDS'}
    assert next(s for s in data if s.serial==1).meetings[1].day=='Tue'
    assert next(s for s in data if s.serial==72).section=='A'
    assert next(s for s in data if s.serial==125).section=='F'
    assert all(s.meetings for s in data)
