import React, { useEffect, useState } from 'react'
import { listTasks, createTask, prioritizeTask } from './api'

export default function App() {
  const [tasks, setTasks] = useState([])
  const [text, setText] = useState('')
  const [nl, setNl] = useState('')
  const [aiRes, setAiRes] = useState(null)

  useEffect(() => { fetchTasks() }, [])

  async function fetchTasks(){
    try{
      const t = await listTasks()
      setTasks(t || [])
    }catch(e){ console.error(e) }
  }

  async function onCreate(e){
    e.preventDefault()
    const payload = { title: text }
    await createTask(payload)
    setText('')
    fetchTasks()
  }

  async function onPrioritize(task){
    const res = await prioritizeTask({ task })
    alert('Score: ' + JSON.stringify(res))
  }

  async function onAiOrder(e){
    e.preventDefault()
    try{
      const out = await window.fetch('/ai/order', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ nl }) })
      const json = await out.json()
      setAiRes(json)
    }catch(err){ console.error(err); alert('AI order failed: ' + err) }
  }

  return (
    <div style={{padding:20,fontFamily:'sans-serif'}}>
      <h1>MCP Orchestrator — Tasks</h1>
      <form onSubmit={onCreate}>
        <input value={text} onChange={e=>setText(e.target.value)} placeholder="Task title" />
        <button type="submit">Create</button>
      </form>

      <h2>Natural-language order (AI)</h2>
      <form onSubmit={onAiOrder}>
        <input value={nl} onChange={e=>setNl(e.target.value)} placeholder="e.g. I want two margherita pizzas and a coke" style={{width:'60%'}} />
        <button type="submit">Order</button>
      </form>
      {aiRes && (
        <div style={{marginTop:10}}>
          <h3>AI Response</h3>
          <pre style={{background:'#fff',padding:10}}>{JSON.stringify(aiRes,null,2)}</pre>
        </div>
      )}

      <ul>
        {tasks.map((t, idx)=> (
          <li key={t.id || idx}>
            {t.title || JSON.stringify(t)}
            <button onClick={()=>onPrioritize(t)}>Prioritize</button>
          </li>
        ))}
      </ul>
    </div>
  )
}
