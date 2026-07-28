import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

const API_BASE = 'http://127.0.0.1:8002'

interface Repository {
  id: number
  url: string
  stars: number | null
  forks: number | null
  credibility_score: number | null
}

function App() {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  const loadRepositories = () => {
    fetch(`${API_BASE}/repositories`)
      .then((response) => response.json())
      .then(setRepositories)
  }

  useEffect(() => {
    loadRepositories()
  }, [])

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)

    const response = await fetch(`${API_BASE}/repositories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    })

    if (!response.ok) {
      const data = await response.json()
      setError(data.detail)
      return
    }

    setUrl('')
    loadRepositories()
  }

  const handleFetch = async (id: number) => {
    await fetch(`${API_BASE}/repositories/${id}/fetch`, { method: 'POST' })
    loadRepositories()
  }

  const handleDelete = async (id: number) => {
    await fetch(`${API_BASE}/repositories/${id}`, { method: 'DELETE' })
    loadRepositories()
  }

  return (
    <div>
      <h1>DevProof</h1>

      <form onSubmit={handleAdd}>
        <input
          type="text"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://github.com/owner/repo"
        />
        <button type="submit">Add repository</button>
      </form>
      {error && <p>{error}</p>}

      <table>
        <thead>
          <tr>
            <th>URL</th>
            <th>Stars</th>
            <th>Forks</th>
            <th>Score</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {repositories.map((repository) => (
            <tr key={repository.id}>
              <td>{repository.url}</td>
              <td>{repository.stars ?? '-'}</td>
              <td>{repository.forks ?? '-'}</td>
              <td>{repository.credibility_score ?? '-'}</td>
              <td>
                <button onClick={() => handleFetch(repository.id)}>Fetch</button>
                <button onClick={() => handleDelete(repository.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App
