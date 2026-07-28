import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

const API_BASE = 'http://127.0.0.1:8002'
const GITHUB_REPO_URL_PATTERN = /^https:\/\/github\.com\/[^/\s]+\/[^/\s]+\/?$/

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
  const [isAdding, setIsAdding] = useState(false)
  const [fetchingId, setFetchingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

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

    if (!GITHUB_REPO_URL_PATTERN.test(url.trim())) {
      setError('Enter a valid GitHub repository URL, e.g. https://github.com/owner/repo')
      return
    }

    setIsAdding(true)
    try {
      const response = await fetch(`${API_BASE}/repositories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() }),
      })

      if (!response.ok) {
        const data = await response.json()
        setError(data.detail)
        return
      }

      setUrl('')
      loadRepositories()
    } finally {
      setIsAdding(false)
    }
  }

  const handleFetch = async (id: number) => {
    setFetchingId(id)
    try {
      await fetch(`${API_BASE}/repositories/${id}/fetch`, { method: 'POST' })
      loadRepositories()
    } finally {
      setFetchingId(null)
    }
  }

  const handleDelete = async (id: number) => {
    setDeletingId(id)
    try {
      await fetch(`${API_BASE}/repositories/${id}`, { method: 'DELETE' })
      loadRepositories()
    } finally {
      setDeletingId(null)
    }
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
          disabled={isAdding}
        />
        <button type="submit" disabled={isAdding}>
          {isAdding ? 'Adding...' : 'Add repository'}
        </button>
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
                <button
                  onClick={() => handleFetch(repository.id)}
                  disabled={fetchingId === repository.id || deletingId === repository.id}
                >
                  {fetchingId === repository.id ? 'Fetching...' : 'Fetch'}
                </button>
                <button
                  onClick={() => handleDelete(repository.id)}
                  disabled={fetchingId === repository.id || deletingId === repository.id}
                >
                  {deletingId === repository.id ? 'Deleting...' : 'Delete'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App
