'use strict';
const $=id=>document.getElementById(id),days=['Sat','Sun','Mon','Tue','Wed','Thu','Fri'];
let sections=[],selected=new Map(),routines=[],warnings=[],controller=null,shown=0,step=0,completed=false,conditionalUsed=false,facultyPrefs=new Map(),displayedRoutines=[];
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const identity=s=>s.program+'|'+s.code;
const conditional=s=>/if\s+required/i.test((s.notes||'')+' '+s.section);
const time=n=>{let h=Math.floor(n/60),m=n%60;return `${h%12||12}:${String(m).padStart(2,'0')} ${h<12?'AM':'PM'}`};
function view(id){step={welcome:0,courses:1,results:2}[id];for(const x of document.querySelectorAll('.view'))x.hidden=x.id!==id;$('progressHeader').hidden=!step;if(step){$('trackFill').style.width=step/2*100+'%';for(const e of document.querySelectorAll('[data-step]'))e.classList.toggle('active',+e.dataset.step<=step)}window.scrollTo({top:0,behavior:'smooth'})}
function modal(title,content){$('modalTitle').textContent=title;$('modalContent').replaceChildren();if(typeof content==='string')$('modalContent').textContent=content;else $('modalContent').append(content);$('modal').hidden=false}
function alertUser(message){modal('Please check your file',message)}
$('modalClose').onclick=()=>{$('modal').hidden=true};$('modal').onclick=e=>{if(e.target===$('modal'))$('modal').hidden=true};
async function loadOfferings(){
 try{
  const response=await fetch('./offerings.json',{cache:'no-store'});
  if(!response.ok)throw Error('Course data is not available right now. Please try again later.');
  const data=await response.json();
  if(!Array.isArray(data.sections)||!data.sections.length)throw Error('No courses are available.');
  sections=data.sections;warnings=data.warnings||[];
  $('termBadge').textContent=data.trimester||'Available offerings';
  const programs=[...new Set(sections.map(s=>s.program).filter(Boolean))].sort();
  $('programFilter').innerHTML='<option value="All">All programs</option>'+programs.map(p=>`<option value="${esc(p)}">${esc(p)}</option>`).join('');
  renderCourses();return true;
 }catch(err){alertUser(err.message);return false}
}
$('start').onclick=async()=>{if(!sections.length){$('start').disabled=true;const ok=await loadOfferings();$('start').disabled=false;if(!ok)return}view('courses')};
$('courseBack').onclick=()=>view('welcome');
$('newSelection').onclick=()=>view('courses');
function courses(){const m=new Map();for(const s of sections){const key=identity(s);if(!m.has(key))m.set(key,[]);m.get(key).push(s)}return m}
function renderCourses(){const all=courses(),filter=$('programFilter').value,q=$('search').value.trim().toLowerCase();$('courseList').replaceChildren();let n=0;for(const [key,group] of all){const s=group[0];if(filter!=='All'&&s.program!==filter)continue;if(!(`${s.code} ${s.title} ${s.program}`).toLowerCase().includes(q))continue;n++;const item=document.createElement('div');item.className='course-item';const desc=document.createElement('div');desc.innerHTML=`<strong>${esc(s.code)} · ${esc(s.title)}</strong><small>${esc(s.program)} · ${group.length} sections</small>`;const add=document.createElement('button');add.className='add';add.textContent=selected.has(key)?'✓':'+';add.disabled=selected.has(key);add.title='Add course';add.onclick=()=>{selected.set(key,group);renderCourses()};item.append(desc,add);$('courseList').append(item)}$('availableCount').textContent=`(${n})`;renderSelected()}
function renderSelected(){$('selectedList').replaceChildren();for(const [key,group] of selected){const s=group[0],item=document.createElement('div');item.className='selected-item';const desc=document.createElement('div');desc.innerHTML=`<strong>${esc(s.code)} · ${esc(s.title)}</strong><small>${esc(s.program)} · ${group.length} sections</small>`;const del=document.createElement('button');del.className='remove';del.textContent='×';del.title='Remove course';del.onclick=()=>{selected.delete(key);facultyPrefs.delete(key);renderCourses()};const pref=document.createElement('div');pref.className='faculty-preferences';const hint=document.createElement('div');hint.className='faculty-pref-label';hint.textContent='Preferred faculty (optional)';pref.append(hint);const names=[...new Set(group.map(z=>(z.faculty||'').trim()).filter(n=>n&&n.toUpperCase()!=='TBA'))].sort((a,b)=>a.localeCompare(b));const active=facultyPrefs.get(key)||new Set();for(const name of names){const option=document.createElement('label');option.className='faculty-choice faculty-choice-vertical';const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=active.has(name);checkbox.onchange=()=>{const chosen=facultyPrefs.get(key)||new Set();if(checkbox.checked)chosen.add(name);else chosen.delete(name);if(chosen.size)facultyPrefs.set(key,chosen);else facultyPrefs.delete(key)};option.append(checkbox,document.createTextNode(name));pref.append(option)}if(!names.length){const no=document.createElement('small');no.textContent='No assigned faculty listed';pref.append(no)}desc.append(pref);item.append(desc,del);$('selectedList').append(item)}$('selectedCount').textContent=`(${selected.size})`;$('generate').disabled=!selected.size}
$('search').oninput=renderCourses;$('programFilter').onchange=renderCourses;
let routineWorker=null;
$('cancel').onclick=()=>{if(routineWorker){routineWorker.terminate();routineWorker=null;controller=null;completed=false;$('generateText').textContent='Cancelled: routine enumeration incomplete.';$('generatePanel').hidden=true;$('generate').disabled=false;if(routines.length){view('results');renderResults()}}};
$('generate').onclick=()=>{
 if(!selected.size)return;
 if(routineWorker){routineWorker.terminate();routineWorker=null}
 routines=[];displayedRoutines=[];fallbackPopupKey='';shown=0;
 $('routines').replaceChildren();completed=false;conditionalUsed=false;
 $('generate').disabled=true;$('generatePanel').hidden=false;
 $('generateText').textContent='Generating conflict-free routines...';$('generateFill').style.width='0%';
 const worker=new Worker('./scheduler-worker.js');routineWorker=worker;let started=false;
 worker.onmessage=e=>{
  if(routineWorker!==worker)return;
  const entry=e.data;
  if(entry.type==='batch'){
   routines.push(...entry.routines);
   if(!started&&routines.length){started=true;view('results');renderResults()}
  }else if(entry.type==='progress'){
   $('generateFill').style.width=entry.fraction+'%';$('generateText').textContent='Generating... '+entry.fraction+'%';
  }else if(entry.type==='done'){
   completed=entry.complete;conditionalUsed=entry.conditional_used;
   worker.terminate();routineWorker=null;
   $('generate').disabled=false;$('generatePanel').hidden=true;
   view('results');renderResults();
  }else if(entry.type==='error'){
   worker.terminate();routineWorker=null;
   $('generate').disabled=false;$('generatePanel').hidden=true;
   alertUser(entry.message);
  }
 };
 worker.onerror=e=>{if(routineWorker!==worker)return;worker.terminate();routineWorker=null;$('generate').disabled=false;$('generatePanel').hidden=true;alertUser('Unable to generate routines in this browser.')};
 worker.postMessage({type:'start',groups:[...selected.values()]});
};
function scoreRoutine(routine){return routine.reduce((count,s)=>count+((facultyPrefs.get(identity(s))||new Set()).has(s.faculty)?1:0),0)}
function entries(routine){const a=[];for(const s of routine)for(const m of s.meetings)a.push({day:m.day,start:m.start,end:m.end,room:m.room,code:s.code,title:s.title,section:s.section,faculty:s.faculty,credit:s.credit,conditional:conditional(s)});return a.sort((a,b)=>days.indexOf(a.day)-days.indexOf(b.day)||a.start-b.start)}
function weeklyGrid(routine){
 const records=entries(routine),activeDays=['Sat','Sun','Mon','Tue','Wed','Thu',...(records.some(x=>x.day==='Fri')?['Fri']:[])];
 const start=Math.min(510,...records.map(x=>x.start)),end=Math.max(990,...records.map(x=>x.end));
 const grid=document.createElement('div');grid.className='weekly-grid';
 const heading=document.createElement('div');heading.className='weekly-heading';
 const totalCredit=routine.reduce((n,s)=>n+(Number(s.credit)||0),0);
 heading.innerHTML='<strong>Class Routine</strong><span>'+routine.length+' courses · '+totalCredit+' credits · '+new Set(records.map(x=>x.day)).size+' class days</span>';grid.append(heading);
 const board=document.createElement('div');board.className='week-board';
 const axis=document.createElement('div');axis.className='week-axis';
 const corner=document.createElement('div');corner.className='week-corner';corner.textContent='DAY / TIME';axis.append(corner);
 const scale=document.createElement('div');scale.className='week-scale';
 const classStarts=[...new Set(records.map(m=>m.start))].sort((a,b)=>a-b);
 const boundaries=[...new Set([start,...classStarts,end])].sort((a,b)=>a-b);
 for(const t of boundaries){const label=document.createElement('span');label.style.left=(t-start)/(end-start)*100+'%';label.textContent=time(t);if(t===start)label.classList.add('week-scale-first');if(t===end)label.classList.add('week-scale-last');scale.append(label)}axis.append(scale);board.append(axis);
 for(const day of activeDays){
  const row=document.createElement('div');row.className='week-row';
  const label=document.createElement('div');label.className='week-day';label.textContent=({Sat:'Saturday',Sun:'Sunday',Mon:'Monday',Tue:'Tuesday',Wed:'Wednesday',Thu:'Thursday',Fri:'Friday'})[day];row.append(label);
  const lane=document.createElement('div');lane.className='week-lane';
  const meetings=records.filter(e=>e.day===day);
  if(!meetings.length)row.classList.add('week-row-empty');
  if(!meetings.length){const empty=document.createElement('span');empty.className='week-empty';empty.textContent='No classes';lane.append(empty)}
  for(const t of boundaries.slice(1,-1)){const line=document.createElement('span');line.className='week-line';line.style.left=(t-start)/(end-start)*100+'%';lane.append(line)}
  meetings.forEach((m,i)=>{
   const block=document.createElement('div');block.className='week-class week-shade-'+(routine.findIndex(s=>s.code===m.code&&s.section===m.section)%6);
   block.style.left=((m.start-start)/(end-start)*100)+'%';
   block.style.width=((m.end-m.start)/(end-start)*100)+'%';
   block.title=[m.code+' · '+m.section,m.title,m.faculty,m.room,time(m.start)+' – '+time(m.end)].join(' | ');
   for(const [className,tag,value] of [['week-course','div',m.code],['week-section','div','Section '+m.section],['week-title','strong',m.title],['week-room','div',m.room?'Room '+m.room:'Room not listed'],['week-faculty','div',m.faculty||'TBA'],['week-period','b',time(m.start)+' – '+time(m.end)]]){const el=document.createElement(tag);el.className=className;el.textContent=value;block.append(el)}
   lane.append(block);
  });row.append(lane);board.append(row);
 }
 grid.append(board);return grid;
}
function table(routine){const wrap=document.createElement('div');wrap.className='table-wrap week-wrap';wrap.append(weeklyGrid(routine));return wrap}

function classDayCount(routine){return new Set(routine.flatMap(s=>(s.meetings||[]).map(m=>m.day))).size}
function timePreferenceScore(routine,mode){
 if(mode==='default')return 0;
 // A class starting exactly at noon is a noon class.
 return routine.reduce((n,s)=>n+(s.meetings||[]).filter(m=>mode==='morning'?m.start<720:m.start>=720).length,0);
}
let fallbackPopupKey='';
function preferredCount(routine){return routine.reduce((count,s)=>{const p=facultyPrefs.get(identity(s));return count+(p&&p.has(s.faculty)?1:0)},0)}
function preferredTarget(){return [...facultyPrefs.values()].filter(set=>set.size).length}
function preferredConflicts(){
 const groups=[...selected.entries()].map(([key,sections])=>({key,sections:sections.filter(s=>(facultyPrefs.get(key)||new Set()).has(s.faculty))})).filter(g=>g.sections.length);
 const result=[],seen=new Set();
 for(let i=0;i<groups.length;i++)for(let j=i+1;j<groups.length;j++){
  for(const a of groups[i].sections)for(const b of groups[j].sections)
   for(const x of a.meetings||[])for(const y of b.meetings||[]){
    const start=Math.max(x.start,y.start),end=Math.min(x.end,y.end);
    if(x.day!==y.day||start>=end)continue;
    const key=[a.program,a.code,a.section,b.program,b.code,b.section,x.day,start,end].join('|');
    if(seen.has(key))continue;seen.add(key);
    result.push(`${a.code} (${a.section}, ${a.faculty}) and ${b.code} (${b.section}, ${b.faculty}) — ${x.day}, ${time(start)}–${time(end)}`);
   }
 }
 return result;
}
function showPreferenceFallback(best,required){
 const wrapper=document.createElement('div');
 const note=document.createElement('p');note.textContent=`No valid routine contains all ${required} selected faculty preferences together. Showing conflict-free routines matching ${best} preferred course${best===1?'':'s'} instead.`;wrapper.append(note);
 const overlaps=preferredConflicts();
 if(overlaps.length){
  const intro=document.createElement('p');intro.textContent='These preferred sections have overlapping class times (possible conflicts):';wrapper.append(intro);
  const list=document.createElement('ul');for(const message of overlaps.slice(0,16)){const li=document.createElement('li');li.textContent=message;list.append(li)}wrapper.append(list);
  if(overlaps.length>16){const more=document.createElement('p');more.textContent=`And ${overlaps.length-16} more overlapping pairs.`;wrapper.append(more)}
 }else{
  const p=document.createElement('p');p.textContent='There is no single direct overlap between the preferred sections found. Their combined choices may still be impossible because of other selected courses or available sections.';wrapper.append(p);
 }
 modal('Faculty preference conflict',wrapper);
}
function getVisibleRoutines(){
 const chosen=[...document.querySelectorAll('.dayChoice:checked')].map(el=>+el.value);
 const all=$('dayAll').checked||!chosen.length,preferred=$('preferredOnly').checked,mode=$('timeSort').value;
 let visible=routines.map((routine,index)=>({routine,index})).filter(item=>{const n=classDayCount(item.routine);return n<=5&&(all||chosen.includes(n))});
 const target=preferredTarget();
 let fallback=false,best=0;
 if(preferred){
  if(!target)visible=[];
  else if(visible.length){
   best=Math.max(...visible.map(item=>preferredCount(item.routine)));
   fallback=best<target;
   visible=visible.filter(item=>preferredCount(item.routine)===best);
  }
 }
 visible.sort((a,b)=>preferredCount(b.routine)-preferredCount(a.routine)||timePreferenceScore(b.routine,mode)-timePreferenceScore(a.routine,mode)||a.index-b.index);
 return {visible,fallback,best,target};
}
function routineCard(item){
 const card=document.createElement('article');card.className='routine-card';
 const top=document.createElement('div');top.className='routine-top';
 const heading=document.createElement('strong');heading.textContent='Routine '+(item.index+1);
 const extras=document.createElement('span');extras.className='routine-meta';extras.textContent=classDayCount(item.routine)+' class days';
 const save=document.createElement('button');save.className='primary';save.textContent='↓ Export';save.onclick=()=>exportDialog(item.routine);
 top.append(heading,extras,save);card.append(top,table(item.routine));return card;
}
function renderResults(){
 const preferenceView=getVisibleRoutines();displayedRoutines=preferenceView.visible;
 shown=0;$('routines').replaceChildren();
 const count=displayedRoutines.length,total=routines.length;
 $('resultCount').textContent=count===total?total.toLocaleString():count.toLocaleString()+' / '+total.toLocaleString();
 $('resultStatus').textContent=!completed?'Generating routines...':total?`Completed · ${total.toLocaleString()} valid routines${conditionalUsed?' · If Required sections considered because no regular-only routine was possible':''}`:'No conflict-free routine was found with the selected courses.';
 const chosen=[...document.querySelectorAll('.dayChoice:checked')].map(el=>+el.value);
 const selectedDays=chosen.map(n=>n+' day'+(n===1?'':'s')).join(' or ');
 const preferred=$('preferredOnly').checked;
 let feedback=count?`Showing ${count.toLocaleString()} of ${total.toLocaleString()} routines`:'';
 if(!count&&total){
   if(!completed)feedback='No matching routine found yet. Generation is still running.';
   else if(preferred&&facultyPrefs.size)feedback='No routine matches all selected preferred faculty'+(!$('dayAll').checked&&chosen.length?' and the selected class-day filters':'')+'. Turn off Preferred Faculty Only or change the day filters to see other routines.';
   else if(!$('dayAll').checked&&chosen.length)feedback=`No routine is possible with ${selectedDays} of classes per week.`;
   else feedback='No routines match these filters.';
 }
 if(preferred&&!facultyPrefs.size)feedback='Select a preferred faculty on the Courses page to use this filter.';
 if(preferred&&preferenceView.fallback)feedback=`No routine matches every preferred faculty. Showing routines with the maximum ${preferenceView.best} of ${preferenceView.target} preferred faculty matches.`;
 if(preferred&&completed&&preferenceView.fallback){const key=[preferenceView.best,preferenceView.target,[...facultyPrefs].map(([k,v])=>k+':'+[...v].sort().join(',')).sort().join('|'),document.querySelectorAll('.dayChoice:checked').length].join('::');if(fallbackPopupKey!==key){fallbackPopupKey=key;showPreferenceFallback(preferenceView.best,preferenceView.target)}}
 $('filterFeedback').textContent=feedback;
 renderMore(20);
}
function renderMore(count=20){
 const end=Math.min(displayedRoutines.length,shown+count);
 while(shown<end){$('routines').append(routineCard(displayedRoutines[shown]));shown++}
 $('more').hidden=shown>=displayedRoutines.length;
 $('more').textContent=`Show more routines (${(displayedRoutines.length-shown).toLocaleString()} remaining) ↓`;
 $('compare').disabled=displayedRoutines.length<2;
}
$('more').onclick=()=>renderMore(20);
$('dayAll').onchange=()=>{
 if($('dayAll').checked)document.querySelectorAll('.dayChoice').forEach(x=>x.checked=false);
 renderResults();
};
document.querySelectorAll('.dayChoice').forEach(box=>box.onchange=()=>{
 const any=[...document.querySelectorAll('.dayChoice')].some(x=>x.checked);
 $('dayAll').checked=!any;
 renderResults();
});
$('preferredOnly').onchange=renderResults;
$('timeSort').onchange=renderResults;
const exportHeaders=['Day','Class Period','Course Code','Course Title','Section','Faculty','Credit','Room'];
function exportRows(routine){
 const records=entries(routine);
 for(let i=0;i<routine.length;i++)for(const other of routine.slice(0,i))for(const a of routine[i].meetings)for(const b of other.meetings)if(a.day===b.day&&Math.max(a.start,b.start)<Math.min(a.end,b.end))throw Error('Cannot export an overlapping routine.');
 let previous='';
 return records.map(e=>{const day=e.day===previous?'':e.day;previous=e.day;return [day,time(e.start)+' – '+time(e.end),e.code,e.title,e.section+(e.conditional?' (If Required)':''),e.faculty||'TBA',e.credit??'Not listed',e.room||'Not listed']});
}
function saveBlob(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000)}
function gridExportRows(routine){
 const records=entries(routine),markers=[...new Set(records.flatMap(x=>[x.start,x.end]))].sort((a,b)=>a-b);
 const headings=markers.slice(0,-1).map((t,i)=>time(t)+'–'+time(markers[i+1]));
 const days=['Sat','Sun','Mon','Tue','Wed','Thu',...(records.some(x=>x.day==='Fri')?['Fri']:[])];
 const cells=days.map(day=>{
  const row=Array(markers.length).fill('');
  row[0]=({Sat:'Saturday',Sun:'Sunday',Mon:'Monday',Tue:'Tuesday',Wed:'Wednesday',Thu:'Thursday'})[day];
  for(const m of records.filter(x=>x.day===day)){
   const col=markers.indexOf(m.start)+1;
   row[col]=[m.code+' · '+m.section,m.title,m.faculty||'TBA',m.room||'Room not listed',time(m.start)+'–'+time(m.end)].join('\n');
  }
  return row;
 });
 return {headings,days,cells,markers,records};
}
async function renderExportCanvas(routine){
 if(!window.html2canvas)throw Error('Image export library could not load. Please check your connection.');
 const stage=document.createElement('div');
 stage.style.cssText='position:fixed;left:-12000px;top:0;width:1600px;padding:20px;background:#fff;z-index:-1';
 const grid=weeklyGrid(routine);grid.style.minWidth='0';stage.append(grid);document.body.append(stage);
 try{return await html2canvas(stage,{backgroundColor:'#ffffff',scale:1.6,width:1600,windowWidth:1800,logging:false})}
 finally{stage.remove()}
}
function exportDialog(routine){
 const div=document.createElement('div'),p=document.createElement('p');p.textContent='Choose the format for this weekly Class Routine.';div.append(p);
 for(const fmt of ['PDF','PNG','XLSX','CSV','JSON','ICS']){
  const b=document.createElement('button');b.className='secondary';b.style.margin='6px';b.textContent=fmt;
  b.onclick=async()=>{
   b.disabled=true;
   try{
    exportRows(routine); // Recheck all meetings for overlaps before exporting.
    const matrix=gridExportRows(routine);
    if(fmt==='JSON'){
     const data={schema:'uiu-section-planner/routine-v1',university:'United International University',trimester:$('termBadge').textContent||null,timezone:'Asia/Dhaka',courses:routine.map(s=>({program:s.program,code:s.code,title:s.title,section:s.section,faculty:s.faculty,faculty_initial:s.initial,credit:s.credit,meetings:(s.meetings||[]).map(m=>({day:m.day,start_minutes:m.start,end_minutes:m.end,start_time:time(m.start),end_time:time(m.end),room:m.room||null}))}))};
     saveBlob(new Blob([JSON.stringify(data,null,2)],{type:'application/json;charset=utf-8'}),'Class_Routine.json');
    }else if(fmt==='ICS'){
     const first=prompt('Enter the first date of classes (YYYY-MM-DD).');
     if(first===null)return;
     const last=prompt('Enter the last date of classes (YYYY-MM-DD).');
     if(last===null)return;
     const validDate=d=>/^\d{4}-\d{2}-\d{2}$/.test(d)&&!Number.isNaN(Date.parse(d+'T00:00:00Z'))&&new Date(d+'T00:00:00Z').toISOString().slice(0,10)===d;
     if(!validDate(first)||!validDate(last)||last<first)throw Error('Please enter valid start and end dates in YYYY-MM-DD format.');
     const dayIndex={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6};
     const origin=new Date(first+'T00:00:00Z'),until=last.replace(/-/g,'')+'T175959Z';
     const pad=n=>String(n).padStart(2,'0');
     const stamp=(date,minutes)=>date.toISOString().slice(0,10).replace(/-/g,'')+'T'+pad(Math.floor(minutes/60))+pad(minutes%60)+'00';
     const safe=v=>String(v??'').replace(/\\/g,'\\\\').replace(/\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');
     const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Section Planner//UIU Weekly Routine//EN','CALSCALE:GREGORIAN','X-WR-TIMEZONE:Asia/Dhaka'];
     let count=0;
     for(const section of routine)for(const meeting of section.meetings||[]){
      const offset=(dayIndex[meeting.day]-origin.getUTCDay()+7)%7;
      const date=new Date(origin.getTime()+offset*86400000);
      if(date.toISOString().slice(0,10)>last)continue;
      const title=section.code+' ('+section.section+') - '+section.title;
      lines.push('BEGIN:VEVENT','UID:uiu-'+Date.now()+'-'+count+++'@section-planner','DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z'),
       'SUMMARY:'+safe(title),'DTSTART;TZID=Asia/Dhaka:'+stamp(date,meeting.start),
       'DTEND;TZID=Asia/Dhaka:'+stamp(date,meeting.end),'RRULE:FREQ=WEEKLY;UNTIL='+until,
       'LOCATION:'+safe(meeting.room||''),'DESCRIPTION:'+safe('Faculty: '+(section.faculty||'TBA')+' | Credit: '+(section.credit||'Not listed')),'END:VEVENT');
     }
     lines.push('END:VCALENDAR');
     saveBlob(new Blob([lines.join('\r\n')+'\r\n'],{type:'text/calendar;charset=utf-8'}),'Class_Routine.ics');
    }else if(fmt==='CSV'){
     const data=[['Class Routine'],['Day / Time',...matrix.headings],...matrix.cells];
     const csv=data.map(line=>line.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');
     saveBlob(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}),'Class_Routine.csv');
    }else if(fmt==='XLSX'){
     if(!window.XLSX)throw Error('Excel export library could not load; check your connection.');
     const data=[['Class Routine'],['Day / Time',...matrix.headings],...matrix.cells];
     const ws=XLSX.utils.aoa_to_sheet(data);
     ws['!cols']=[{wch:15},...matrix.headings.map(()=>({wch:24}))];
     ws['!rows']=[{hpt:35},{hpt:30},...matrix.cells.map(row=>({hpt:row.slice(1).some(Boolean)?110:28}))];
     ws['!merges']=[];
     for(let i=0;i<matrix.days.length;i++){
      const day=matrix.days[i],row=matrix.cells[i];
      for(const m of matrix.records.filter(x=>x.day===day)){
       const from=matrix.markers.indexOf(m.start)+1,to=matrix.markers.indexOf(m.end);
       if(to>from)ws['!merges'].push({s:{r:i+2,c:from},e:{r:i+2,c:to}});
      }
     }
     const wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,ws,'Weekly Routine');
     XLSX.writeFile(wb,'Class_Routine.xlsx');
    }else if(fmt==='PNG'){
     const canvas=await renderExportCanvas(routine);
     const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));
     if(!blob)throw Error('Unable to render PNG.');saveBlob(blob,'Class_Routine.png');
    }else{
     if(!window.jspdf?.jsPDF)throw Error('PDF export library could not load; check your connection.');
     const canvas=await renderExportCanvas(routine);
     const doc=new window.jspdf.jsPDF({orientation:'landscape',format:'a3'});
     const pw=doc.internal.pageSize.getWidth(),ph=doc.internal.pageSize.getHeight();
     const ratio=Math.min((pw-14)/canvas.width,(ph-14)/canvas.height);
     const w=canvas.width*ratio,h=canvas.height*ratio;
     doc.addImage(canvas.toDataURL('image/png'),'PNG',(pw-w)/2,(ph-h)/2,w,h);
     doc.save('Class_Routine.pdf');
    }
    $('modal').hidden=true;
   }catch(err){alertUser(err.message)}finally{b.disabled=false}
  };div.append(b);
 }
 modal('Export Class Routine',div);
}
$('compare').onclick=()=>{const div=document.createElement('div');const p=document.createElement('p');p.textContent='Select 2 or more visible routines to compare side by side.';div.append(p);const list=document.createElement('div');list.style.maxHeight='320px';list.style.overflow='auto';displayedRoutines.forEach((item,i)=>{const l=document.createElement('label');l.className='choice';const c=document.createElement('input');c.type='checkbox';c.value=i;l.append(c,document.createTextNode('Routine '+(item.index+1)));list.append(l)});div.append(list);const b=document.createElement('button');b.className='primary';b.style.marginTop='16px';b.textContent='Compare selected';b.onclick=()=>{const indices=[...list.querySelectorAll(':checked')].map(x=>+x.value);if(indices.length<2){alert('Select at least 2 routines.');return}const display=document.createElement('div');display.className='compare-grid';for(const i of indices){const item=displayedRoutines[i];const card=document.createElement('div');const h=document.createElement('h3');h.textContent='Routine '+(item.index+1);card.append(h,table(item.routine));display.append(card)}modal('Routine comparison',display)};div.append(b);modal('Compare routines',div)};
view('welcome');
