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
  analysis_report: AnalysisReport | null
}

interface GithubRepoSummary {
  name: string
  full_name: string
  html_url: string
  description: string | null
  stargazers_count: number
  language: string | null
}

interface ReportCategory {
  name: string
  score: number
  comment: string
}

interface AnalysisReport {
  overall_score: number
  categories: ReportCategory[]
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  learning_roadmap: string[]
}

function App() {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [url, setUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isAdding, setIsAdding] = useState(false)
  const [fetchingId, setFetchingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const [username, setUsername] = useState('')
  const [githubRepos, setGithubRepos] = useState<GithubRepoSummary[]>([])
  const [isLoadingRepos, setIsLoadingRepos] = useState(false)
  const [usernameError, setUsernameError] = useState<string | null>(null)
  const [selectingUrl, setSelectingUrl] = useState<string | null>(null)
  const [activeRepositoryId, setActiveRepositoryId] = useState<number | null>(null)

  const loadRepositories = () => {
    return fetch(`${API_BASE}/repositories`)
      .then((response) => response.json())
      .then((data: Repository[]) => {
        setRepositories(data)
        return data
      })
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

  const handleLoadGithubRepos = async (event: FormEvent) => {
    event.preventDefault()
    setUsernameError(null)
    setGithubRepos([])
    setIsLoadingRepos(true)
    try {
      const response = await fetch(`${API_BASE}/github/${username.trim()}/repos`)
      if (!response.ok) {
        const data = await response.json()
        setUsernameError(data.detail)
        return
      }
      setGithubRepos(await response.json())
    } finally {
      setIsLoadingRepos(false)
    }
  }

  const handleSelectRepo = async (repo: GithubRepoSummary) => {
    setSelectingUrl(repo.html_url)
    setUsernameError(null)
    try {
      const createResponse = await fetch(`${API_BASE}/repositories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: repo.html_url }),
      })

      let repositoryId: number
      if (createResponse.status === 409) {
        const allRepos = await loadRepositories()
        const existing = allRepos.find((candidate) => candidate.url === repo.html_url)
        if (!existing) {
          setUsernameError('Repository already exists but could not be located.')
          return
        }
        repositoryId = existing.id
      } else if (!createResponse.ok) {
        const data = await createResponse.json()
        setUsernameError(data.detail)
        return
      } else {
        repositoryId = (await createResponse.json()).id
      }

      const analyzeResponse = await fetch(`${API_BASE}/repositories/${repositoryId}/analyze`, {
        method: 'POST',
      })

      if (!analyzeResponse.ok) {
        const data = await analyzeResponse.json()
        setUsernameError(data.detail)
        return
      }

      setActiveRepositoryId(repositoryId)
      await loadRepositories()
    } finally {
      setSelectingUrl(null)
    }
  }

  const activeRepository = repositories.find((repository) => repository.id === activeRepositoryId)
  const activeReport = activeRepository?.analysis_report ?? null

  return (
    <div>
      <h1>DevProof</h1>

      <section>
        <h2>Analyze a developer's GitHub repository</h2>
        <form onSubmit={handleLoadGithubRepos}>
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="GitHub username"
            disabled={isLoadingRepos}
          />
          <button type="submit" disabled={isLoadingRepos}>
            {isLoadingRepos ? 'Loading...' : 'Load repositories'}
          </button>
        </form>
        {usernameError && <p>{usernameError}</p>}

        {githubRepos.length > 0 && (
          <ul>
            {githubRepos.map((repo) => (
              <li key={repo.full_name}>
                {repo.full_name} ({repo.stargazers_count} stars, {repo.language ?? 'unknown language'})
                {' '}
                <button
                  onClick={() => handleSelectRepo(repo)}
                  disabled={selectingUrl !== null}
                >
                  {selectingUrl === repo.html_url ? 'Analyzing...' : 'Select'}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {activeReport && (
        <section>
          <h2>Engineering Readiness Report: {activeRepository?.url}</h2>
          <p>Overall score: {activeReport.overall_score}/100</p>

          <h3>Categories</h3>
          <ul>
            {activeReport.categories.map((category) => (
              <li key={category.name}>
                <strong>{category.name}: {category.score}/100</strong> — {category.comment}
              </li>
            ))}
          </ul>

          <h3>Strengths</h3>
          <ul>
            {activeReport.strengths.map((item) => <li key={item}>{item}</li>)}
          </ul>

          <h3>Weaknesses</h3>
          <ul>
            {activeReport.weaknesses.map((item) => <li key={item}>{item}</li>)}
          </ul>

          <h3>Recommendations</h3>
          <ul>
            {activeReport.recommendations.map((item) => <li key={item}>{item}</li>)}
          </ul>

          <h3>Learning Roadmap</h3>
          <ul>
            {activeReport.learning_roadmap.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
      )}

      <section>
        <h2>Add a repository directly</h2>
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
                  <button onClick={() => setActiveRepositoryId(repository.id)}>
                    View Report
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default App
