const API_ROOT = (import.meta.env.VITE_API_ROOT) || ''

async function call(path, opts){
  const res = await fetch(API_ROOT + path, opts)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function listTasks(){ return call('/tasks', { headers: {'X-API-Key': ''} }) }
export function createTask(payload){ return call('/tasks', { method: 'POST', headers: {'Content-Type':'application/json','X-API-Key':''}, body: JSON.stringify(payload) }) }
export function prioritizeTask(payload){ return call('/prioritize', { method: 'POST', headers: {'Content-Type':'application/json','X-API-Key':''}, body: JSON.stringify(payload) }) }
