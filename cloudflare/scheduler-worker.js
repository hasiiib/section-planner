'use strict';
let cancelled=false;
const ident=s=>s.program+'|'+s.code+'|'+s.section;
const conditional=s=>/if\s+required/i.test((s.notes||'')+' '+s.section+' '+(s.uncertain||[]).join(' '));
const bad=s=>!s.meetings?.length||s.meetings.some(m=>!(m.end>m.start))||(s.uncertain||[]).some(x=>/time|weekday|meeting/i.test(x));
function run(groups,regularOnly){
 const chosen=[],seen=new Set(),batch=[];let valid=0,rejected=0,root=0;
 const choices=groups.map(group=>regularOnly?group.filter(s=>!conditional(s)):group);
 if(choices.some(g=>!g.length))return {valid:0,rejected:0,complete:true};
 const flush=()=>{if(batch.length)postMessage({type:'batch',routines:batch.splice(0)})};
 function walk(depth){
  if(cancelled)return false;
  if(depth===choices.length){valid++;batch.push(chosen.slice());if(batch.length>=40)flush();return true}
  const local=new Set();
  for(const s of choices[depth]){
   if(cancelled)return false;
   const key=ident(s);
   if(local.has(key))continue;local.add(key);
   if(bad(s)){rejected++;continue}
   let conflict=false;
   for(const other of chosen){for(const a of s.meetings)for(const b of other.meetings){if(a.day===b.day&&Math.max(a.start,b.start)<Math.min(a.end,b.end)){conflict=true;break}}if(conflict)break}
   if(conflict){rejected++;continue}
   chosen.push(s);const ok=walk(depth+1);chosen.pop();
   if(!ok)return false;
   if(depth===0){root++;postMessage({type:'progress',fraction:Math.round(root/choices[0].length*100)})}
  }
  return true;
 }
 const complete=walk(0);flush();return {valid,rejected,complete};
}
onmessage=e=>{
 if(e.data.type!=='start')return;
 try{
  const groups=e.data.groups;
  if(!groups.length||groups.length>20||groups.some(g=>!g.length||g.length>250))throw Error('Select between 1 and 20 courses with valid sections.');
  if(new Set(groups.map(g=>g[0].program+'|'+g[0].code)).size!==groups.length)throw Error('Duplicate course selected.');
  for(const g of groups)if(g.some(s=>s.program!==g[0].program||s.code!==g[0].code))throw Error('Invalid course sections.');
  const canRegular=groups.every(g=>g.some(s=>!conditional(s)));
  let first=canRegular?run(groups,true):{valid:0,rejected:0,complete:true};
  if(first.valid||!first.complete)postMessage({type:'done',valid:first.valid,rejected_branches:first.rejected,complete:first.complete,conditional_used:false});
  else{postMessage({type:'progress',fraction:0});const second=run(groups,false);postMessage({type:'done',valid:second.valid,rejected_branches:second.rejected+first.rejected,complete:second.complete,conditional_used:true})}
 }catch(err){postMessage({type:'error',message:err.message})}
};
