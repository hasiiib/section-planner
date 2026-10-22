import csv
import io
import json
from fastapi.testclient import TestClient
from webapp import app
from uiu.model import Section, Meeting
from uiu.scheduler import generate_preferred

client=TestClient(app)

def sec(course,section,day,start=510,end=590,notes=''):
    return Section('BSCSE',course,course,section,'TBA','','3',(Meeting(day,start,end,'101'),),notes=notes)

def test_regular_preferred():
    a=sec('CSE 1111','A','Sat');b=sec('CSE 1111','BB','Sun',notes='If Required')
    c=sec('CSE 1112','A','Sun')
    records=[]
    stats=generate_preferred([[a,b],[c]],records.append)
    assert stats[0]==1 and not stats[3] and records[0][0].section=='A'

def test_conditional_fallback():
    a=sec('CSE 1111','A','Sat');b=sec('CSE 1111','BB','Sun',notes='If Required')
    c=sec('CSE 1112','A','Sat')
    records=[]
    stats=generate_preferred([[a,b],[c]],records.append)
    assert stats[0]==1 and stats[3] and records[0][0].section=='BB'

def test_web_home_health():
    assert client.get('/').status_code==200
    assert 'Section Planner' in client.get('/').text
    assert client.get('/api/health').json()=={'status':'ok'}

def test_web_import_export():
    rows=[['Program','Course Code','Title','Section','Day1','Time1','Faculty Name'],['BSCSE','CSE 1111','Programming','A','Sat','08:30:AM - 09:50:AM','TBA']]
    f=io.StringIO();csv.writer(f).writerows(rows)
    result=client.post('/api/import',files={'file':('offerings.csv',f.getvalue().encode(),'text/csv')})
    assert result.status_code==200,result.text
    data=result.json();assert len(data['sections'])==1
    response=client.post('/api/export',json={'sections':data['sections'],'format':'csv'})
    assert response.status_code==200 and b'Class Routine' in response.content

def test_web_generate():
    x=sec('CSE 1111','A','Sat').to_dict();y=sec('CSE 1112','A','Sun').to_dict()
    r=client.post('/api/generate',json={'groups':[[x],[y]]})
    assert r.status_code==200
    events=[json.loads(t) for t in r.text.splitlines()]
    assert any(x['type']=='routine' for x in events)
    assert next(x for x in events if x['type']=='done')['valid']==1

def test_unsupported():
    r=client.post('/api/import',files={'file':('test.exe',b'x','application/octet-stream')})
    assert r.status_code==400
