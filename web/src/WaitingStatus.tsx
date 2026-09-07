import {useEffect,useState} from 'react';
import {Clock3,AlertCircle,RefreshCw} from 'lucide-react';
import {waitingText,type PendingJob} from './waiting';

export function WaitingStatus({jobs,mode,now,retry}:{jobs:PendingJob[];mode:string;now:number;retry:(id:string)=>void}) {
  const [elapsed,setElapsed]=useState(0);
  useEffect(()=>{
    const start=performance.now();setElapsed(0);
    const timer=setInterval(()=>setElapsed((performance.now()-start)/1000),1000);
    return ()=>clearInterval(timer);
  },[now]);
  const job=jobs.find(j=>j.status==='error')||jobs.find(j=>j.status==='generating')||jobs[0];
  if(!job)return null;
  const failed=job.status==='error';
  return <div className={`waiting-status ${failed?'failed':''}`} role="status">
    {failed?<AlertCircle size={14}/>:<Clock3 size={14}/>}
    <span>{waitingText(job,mode,now+elapsed)}</span>
    {failed&&job.id&&<button type="button" onClick={()=>retry(job.id!)}><RefreshCw size={12}/>重试</button>}
  </div>;
}
