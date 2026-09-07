export type PendingJob = {id?:string;status:string;reason?:string;due?:number;error?:string};

export function waitingText(job:PendingJob, mode:string, now:number):string {
  if(job.status==='error') return '回复生成失败 · 消息已保留，可重试';
  if(job.status==='generating') return mode==='live'?'模型请求中 · 正在生成回复':'正在处理体验回复';
  if(job.reason==='paused') return '故事已暂停 · 消息会在继续后处理';
  if(job.due!==undefined && now>job.due+90) return '等待处理已超出预期 · 请检查本地服务状态';
  const labels:Record<string,string>={
    first_contact:'首次对话 · 即将请求模型',
    busy:'作息等待 · 角色当前处于忙碌时段',
    sleep:'作息等待 · 角色正在休息，醒来后再处理',
    character_delay:'已读 · 角色选择稍后回应',
    retry:'等待重试 · 不会重复发送你的消息',
  };
  return labels[job.reason||'']||'消息已保存 · 等待处理';
}
