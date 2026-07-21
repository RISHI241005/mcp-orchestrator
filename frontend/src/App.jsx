import React, { useEffect, useState } from 'react'
import { listTasks, createTask, prioritizeTask } from './api'

export default function App() {
  const [tasks, setTasks] = useState([])
  const [text, setText] = useState('')

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

  return (
    <div style={{padding:20,fontFamily:'sans-serif'}}>
      <h1>MCP Orchestrator — Tasks</h1>
      <form onSubmit={onCreate}>
        <input value={text} onChange={e=>setText(e.target.value)} placeholder="Task title" />
        <button type="submit">Create</button>
      </form>
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
