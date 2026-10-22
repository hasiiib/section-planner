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
  const response=await fetch('/api/offerings',{cache:'no-store'});
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
function renderSelected(){$('selectedList').replaceChildren();for(const [key,group] of selected){const s=group[0],item=document.createElement('div');item.className='selected-item';const desc=document.createElement('div');const detail=group.map(z=>z.section+(conditional(z)?' (If Required)':'')+': '+z.meetings.map(m=>`${m.day} ${time(m.start)}–${time(m.end)}`).join(', ')).join('  •  ');desc.innerHTML=`<strong>${esc(s.code)} · ${esc(s.title)}</strong><small>${esc(s.program)} · ${group.length} sections</small><small>${esc(detail)}</small>`;const del=document.createElement('button');del.className='remove';del.textContent='×';del.title='Remove course';del.onclick=()=>{selected.delete(key);facultyPrefs.delete(key);renderCourses()};const pref=document.createElement('div');pref.className='faculty-preferences';const hint=document.createElement('div');hint.className='faculty-pref-label';hint.textContent='Preferred faculty (optional)';pref.append(hint);const names=[...new Set(group.map(z=>(z.faculty||'').trim()).filter(n=>n&&n.toUpperCase()!=='TBA'))].sort((a,b)=>a.localeCompare(b));const active=facultyPrefs.get(key)||new Set();for(const name of names){const option=document.createElement('label');option.className='faculty-choice';const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.checked=active.has(name);checkbox.onchange=()=>{const chosen=facultyPrefs.get(key)||new Set();if(checkbox.checked)chosen.add(name);else chosen.delete(name);if(chosen.size)facultyPrefs.set(key,chosen);else facultyPrefs.delete(key)};option.append(checkbox,document.createTextNode(name));pref.append(option)}if(!names.length){const no=document.createElement('small');no.textContent='No assigned faculty listed';pref.append(no)}desc.append(pref);item.append(desc,del);$('selectedList').append(item)}$('selectedCount').textContent=`(${selected.size})`;$('generate').disabled=!selected.size}
$('search').oninput=renderCourses;$('programFilter').onchange=renderCourses;
$('cancel').onclick=()=>{if(controller){controller.abort();controller=null;$('generateText').textContent='Cancelled. Generated routines were incomplete.';$('generate').disabled=false;$('generatePanel').hidden=true}};
$('generate').onclick=async()=>{if(!selected.size)return;routines=[];displayedRoutines=[];shown=0;$('routines').replaceChildren();completed=false;conditionalUsed=false;controller=new AbortController();$('generate').disabled=true;$('generatePanel').hidden=false;$('generateText').textContent='Generating conflict-free routines...';$('generateFill').style.width='0%';
 let lastStatus=null;try{const response=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({groups:[...selected.values()]}),signal:controller.signal});if(!response.ok){let data=await response.json();throw Error(data.detail||'Generation failed')}
 const reader=response.body.getReader(),decoder=new TextDecoder();let pending='';while(true){const {value,done}=await reader.read();if(done)break;pending+=decoder.decode(value,{stream:true});let pos;while((pos=pending.indexOf('\n'))>=0){const line=pending.slice(0,pos);pending=pending.slice(pos+1);if(!line.trim())continue;const entry=JSON.parse(line);if(entry.type==='routine'){routines.push(entry.sections);if(routines.length===1&&step!==2){view('results');renderResults()};if(routines.length<=20)renderResults()}else if(entry.type==='progress'){$('generateFill').style.width=entry.fraction+'%';$('generateText').textContent=`Generating... ${entry.fraction}%`;}else if(entry.type==='done'){lastStatus=entry;completed=entry.complete;conditionalUsed=entry.conditional_used}else if(entry.type==='error')throw Error(entry.message)}}
 if(!lastStatus)throw Error('Generation stopped before completion');view('results');renderResults(true);
 }catch(err){if(err.name==='AbortError'){$('generatePanel').hidden=true;return}alertUser(err.message)}finally{controller=null;$('generate').disabled=false;$('generatePanel').hidden=true}}
function scoreRoutine(routine){return routine.reduce((count,s)=>count+((facultyPrefs.get(identity(s))||new Set()).has(s.faculty)?1:0),0)}
function entries(routine){const a=[];for(const s of routine)for(const m of s.meetings)a.push({day:m.day,start:m.start,end:m.end,room:m.room,code:s.code,title:s.title,section:s.section,faculty:s.faculty,credit:s.credit,conditional:conditional(s)});return a.sort((a,b)=>days.indexOf(a.day)-days.indexOf(b.day)||a.start-b.start)}
function table(routine){const rows=entries(routine),wrap=document.createElement('div');wrap.className='table-wrap';const table=document.createElement('table');table.innerHTML='<thead><tr>'+['Day','Class Period','Course Code','Course Title','Section','Faculty','Credit','Room'].map(x=>`<th>${x}</th>`).join('')+'</tr></thead>';const body=document.createElement('tbody');for(let i=0;i<rows.length;i++){const e=rows[i],tr=document.createElement('tr');if(i===0||e.day!==rows[i-1].day){let count=1;while(rows[i+count]&&rows[i+count].day===e.day)count++;const day=document.createElement('td');day.className='day';day.rowSpan=count;day.textContent=e.day;tr.append(day)}for(const val of [`${time(e.start)} – ${time(e.end)}`,e.code,e.title,e.section+(e.conditional?' (If Required)':''),e.faculty||'TBA',e.credit===null||e.credit===undefined||e.credit===''?'Not listed':String(e.credit),e.room||'Not listed']){const td=document.createElement('td');td.textContent=val;tr.append(td)}body.append(tr)}table.append(body);wrap.append(table);return wrap}
function classDayCount(routine){return new Set(routine.flatMap(s=>(s.meetings||[]).map(m=>m.day))).size}
function timePreferenceScore(routine,mode){
 if(mode==='default')return 0;
 // A class starting exactly at noon is a noon class.
 return routine.reduce((n,s)=>n+(s.meetings||[]).filter(m=>mode==='morning'?m.start<720:m.start>=720).length,0);
}
function getVisibleRoutines(){
 const chosen=[...document.querySelectorAll('.dayChoice:checked')].map(el=>+el.value);
 const all=$('dayAll').checked||!chosen.length;
 const preferred=$('preferredOnly').checked;
 const mode=$('timeSort').value;
 const rows=routines.map((routine,index)=>({routine,index}));
 const visible=rows.filter(item=>{
  const dayCount=classDayCount(item.routine);
  if(dayCount>5||!(all||chosen.includes(dayCount)))return false;
  if(!preferred)return true;
  // Every course with an explicit faculty preference must use one of its selected teachers.
  // Courses without preferences remain unrestricted.
  if(!facultyPrefs.size)return false;
  return item.routine.every(section=>{
    const allowed=facultyPrefs.get(identity(section));
    return !allowed||!allowed.size||allowed.has(section.faculty);
  });
 });
 // Sort the matching results; the preferred-only toggle intentionally filters.
 visible.sort((a,b)=>scoreRoutine(b.routine)-scoreRoutine(a.routine)||timePreferenceScore(b.routine,mode)-timePreferenceScore(a.routine,mode)||a.index-b.index);
 return visible;
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
 displayedRoutines=getVisibleRoutines();
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
function exportDialog(routine){const div=document.createElement('div');const p=document.createElement('p');p.textContent='Choose the format for this Class Routine.';div.append(p);for(const fmt of ['PDF','PNG','XLSX','CSV']){const b=document.createElement('button');b.className='secondary';b.style.margin='6px';b.textContent=fmt;b.onclick=async()=>{b.disabled=true;try{const r=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sections:routine,format:fmt.toLowerCase()})});if(!r.ok){const data=await r.json();throw Error(data.detail||'Export failed')}const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Class_Routine.'+fmt.toLowerCase();document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);$('modal').hidden=true}catch(e){alertUser(e.message)}finally{b.disabled=false}};div.append(b)}modal('Export Class Routine',div)}
$('compare').onclick=()=>{const div=document.createElement('div');const p=document.createElement('p');p.textContent='Select 2 or more visible routines to compare side by side.';div.append(p);const list=document.createElement('div');list.style.maxHeight='320px';list.style.overflow='auto';displayedRoutines.forEach((item,i)=>{const l=document.createElement('label');l.className='choice';const c=document.createElement('input');c.type='checkbox';c.value=i;l.append(c,document.createTextNode('Routine '+(item.index+1)));list.append(l)});div.append(list);const b=document.createElement('button');b.className='primary';b.style.marginTop='16px';b.textContent='Compare selected';b.onclick=()=>{const indices=[...list.querySelectorAll(':checked')].map(x=>+x.value);if(indices.length<2){alert('Select at least 2 routines.');return}const display=document.createElement('div');display.className='compare-grid';for(const i of indices){const item=displayedRoutines[i];const card=document.createElement('div');const h=document.createElement('h3');h.textContent='Routine '+(item.index+1);card.append(h,table(item.routine));display.append(card)}modal('Routine comparison',display)};div.append(b);modal('Compare routines',div)};
view('welcome');
