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

  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [fetchingId, setFetchingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const loadRepositories = async () => {
    try {
      const response = await fetch(`${API_BASE}/repositories`)

      if (!response.ok) {
        throw new Error('Could not load repositories')
      }

      const data = await response.json()
      setRepositories(data)
    } catch {
      setError('Could not load repositories. Make sure the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadRepositories()
  }, [])

  const handleAdd = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsAdding(true)

    try {
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
      await loadRepositories()
    } catch {
      setError('Could not add repository. Make sure the backend is running.')
    } finally {
      setIsAdding(false)
    }
  }

  const handleFetch = async (id: number) => {
    setError(null)
    setFetchingId(id)

    try {
      const response = await fetch(`${API_BASE}/repositories/${id}/fetch`, {
        method: 'POST',
      })

      if (!response.ok) {
        const data = await response.json()
        setError(data.detail)
        return
      }

      await loadRepositories()
    } catch {
      setError('Could not fetch repository data.')
    } finally {
      setFetchingId(null)
    }
  }

  const handleDelete = async (id: number) => {
    setError(null)
    setDeletingId(id)

    try {
      const response = await fetch(`${API_BASE}/repositories/${id}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const data = await response.json()
        setError(data.detail)
        return
      }

      await loadRepositories()
    } catch {
      setError('Could not delete repository.')
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

      {isLoading ? (
        <p>Loading repositories...</p>
      ) : repositories.length === 0 ? (
        <p>No repositories have been added yet.</p>
      ) : (
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
                    disabled={
                      fetchingId === repository.id ||
                      deletingId === repository.id
                    }
                  >
                    {fetchingId === repository.id ? 'Fetching...' : 'Fetch'}
                  </button>

                  <button
                    onClick={() => handleDelete(repository.id)}
                    disabled={
                      deletingId === repository.id ||
                      fetchingId === repository.id
                    }
                  >
                    {deletingId === repository.id ? 'Deleting...' : 'Delete'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default App