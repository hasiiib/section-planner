"""Browser edition of Section Planner. The schedule engine remains on the server."""
import io
import json
import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from uiu.importers import import_offerings, SUPPORTED
from uiu.model import Section
from uiu.scheduler import generate_preferred, verify
from uiu.exports import export

BASE=Path(__file__).resolve().parent
app=FastAPI(title='Section Planner',docs_url=None,redoc_url=None)
app.mount('/static',StaticFiles(directory=BASE/'web_static'),name='static')

@app.get('/',response_class=HTMLResponse)
def index():
    return (BASE/'web_static/index.html').read_text(encoding='utf8')

@app.get('/api/health')
def health():return {'status':'ok'}

@app.post('/api/import')
async def upload(file:UploadFile=File(...)):
    name=Path(file.filename or 'upload').name
    suffix=Path(name).suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(400,'Unsupported file. Upload PDF, DOC, DOCX, XLS, XLSX or CSV.')
    # Prevent accidental server exhaustion from arbitrarily large uploads.
    size=0
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/('offering'+suffix)
        with path.open('wb') as f:
            while part:=await file.read(1024*1024):
                size+=len(part)
                if size>20*1024*1024:raise HTTPException(413,'File is too large. Maximum size is 20 MB.')
                f.write(part)
        try:sections,warnings,pages,trimester=import_offerings(path)
        except Exception as e:raise HTTPException(400,f'Could not read a valid class schedule: {e}') from e
    usable=[s for s in sections if s.meetings and not any('time' in n.lower() or 'weekday' in n.lower() or 'meeting' in n.lower() for n in s.uncertain)]
    if not usable:raise HTTPException(400,'No usable class periods were found. Upload a valid course-offering file.')
    return {'sections':[s.to_dict() for s in usable], 'warnings':warnings,'pages':pages,'trimester':trimester,'filename':name}

class GenerateBody(BaseModel):
    groups:list[list[dict]]

@app.post('/api/generate')
def generate(body:GenerateBody, request:Request):
    try:groups=[[Section.from_dict(s) for s in group] for group in body.groups]
    except (TypeError,ValueError,KeyError) as e:raise HTTPException(400,f'Invalid course selection: {e}')
    if not groups or len(groups)>20 or any(not group or len(group)>250 for group in groups):
        raise HTTPException(400,'Select between 1 and 20 courses, each with available sections.')
    identities=[(g[0].program,g[0].code) for g in groups]
    if len(set(identities))!=len(identities) or any(any((s.program,s.code)!=identities[i] for s in g) for i,g in enumerate(groups)):
        raise HTTPException(400,'A course is duplicated or its sections do not match.')
    # Stream every solution, never silently truncate. Browser can abort the request.
    # The iterator uses a background thread to keep the async web server responsive.
    import queue,threading
    q=queue.Queue(maxsize=128)
    stopped=threading.Event()
    def put(item):
        while not stopped.is_set():
            try:q.put(item,timeout=.25);return
            except queue.Full:continue
    def job():
        try:
            def found(routine):put({'type':'routine','sections':[s.to_dict() for s in routine]})
            valid,rejected,complete,conditional=generate_preferred(groups,found,cancelled=stopped.is_set,
                on_progress=lambda n,t:put({'type':'progress','fraction':round(100*n/t) if t else 0}))
            put({'type':'done','valid':valid,'rejected_branches':rejected,'complete':complete,'conditional_used':conditional})
        except Exception as e:put({'type':'error','message':str(e)})
        finally:put(None)
    threading.Thread(target=job,daemon=True).start()
    def stream():
        try:
            while True:
                item=q.get()
                if item is None:break
                yield json.dumps(item,ensure_ascii=False)+'\n'
        finally:stopped.set()
    return StreamingResponse(stream(),media_type='application/x-ndjson',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

class ExportBody(BaseModel):
    sections:list[dict]
    format:str

@app.post('/api/export')
def export_one(body:ExportBody):
    suffix='.'+body.format.lower().lstrip('.')
    types={'.pdf':'application/pdf','.png':'image/png','.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.csv':'text/csv; charset=utf-8'}
    if suffix not in types:raise HTTPException(400,'Choose PDF, PNG, XLSX or CSV.')
    try:
        routine=[Section.from_dict(x) for x in body.sections]
        if not routine or len(routine)>20 or verify(routine):raise ValueError('Cannot export an invalid routine.')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/('Class_Routine'+suffix)
            export(routine,path)
            content=path.read_bytes()
    except (ValueError,KeyError,TypeError) as e:raise HTTPException(400,str(e))
    return Response(content,media_type=types[suffix],headers={'Content-Disposition':f'attachment; filename="Class_Routine{suffix}"'})
