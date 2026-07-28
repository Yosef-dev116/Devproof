import { useEffect, useState } from 'react'

function App() {
  const [status, setStatus] = useState('checking backend...')

  useEffect(() => {
    fetch('http://127.0.0.1:8002/health')
      .then((response) => response.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('backend unreachable'))
  }, [])

  return (
    <div>
      <h1>DevProof</h1>
      <p>Backend status: {status}</p>
    </div>
  )
}

export default App
