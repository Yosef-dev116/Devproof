import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8002'
const GITHUB_REPO_URL_PATTERN = /^https:\/\/github\.com\/[^/\s]+\/[^/\s]+\/?$/

interface CurrentUser {
  github_username: string
  avatar_url: string | null
}

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
  details: string
}

interface AnalysisReport {
  overall_score: number
  categories: ReportCategory[]
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  learning_roadmap: string[]
}

function scoreTier(score: number): 'high' | 'medium' | 'low' {
  if (score >= 80) return 'high'
  if (score >= 50) return 'medium'
  return 'low'
}

function ScoreBadge({ score }: { score: number }) {
  return <span className={`score-badge score-${scoreTier(score)}`}>{score}</span>
}

function App() {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null)
  const [checkingAuth, setCheckingAuth] = useState(true)

  const [repositories, setRepositories] = useState<Repository[]>([])
  const [fetchingId, setFetchingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [analyzingId, setAnalyzingId] = useState<number | null>(null)

  const [query, setQuery] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [githubRepos, setGithubRepos] = useState<GithubRepoSummary[]>([])
  const [selectingUrl, setSelectingUrl] = useState<string | null>(null)
  const [activeRepositoryId, setActiveRepositoryId] = useState<number | null>(null)
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null)

  const apiFetch = async (path: string, options?: RequestInit) => {
    const response = await fetch(`${API_BASE}${path}`, { ...options, credentials: 'include' })
    if (response.status === 401) {
      setCurrentUser(null)
    }
    return response
  }

  const loadRepositories = () => {
    return apiFetch('/repositories')
      .then((response) => response.json())
      .then((data: Repository[]) => {
        setRepositories(data)
        return data
      })
  }

  useEffect(() => {
    apiFetch('/auth/me')
      .then((response) => (response.ok ? response.json() : null))
      .then((user: CurrentUser | null) => {
        setCurrentUser(user)
        setCheckingAuth(false)
        if (user) loadRepositories()
      })
  }, [])

  const handleLogout = async () => {
    await apiFetch('/auth/logout', { method: 'POST' })
    setCurrentUser(null)
    setRepositories([])
  }

  const handleFetch = async (id: number) => {
    setFetchingId(id)
    try {
      await apiFetch(`/repositories/${id}/fetch`, { method: 'POST' })
      loadRepositories()
    } finally {
      setFetchingId(null)
    }
  }

  const handleDelete = async (id: number) => {
    setDeletingId(id)
    try {
      await apiFetch(`/repositories/${id}`, { method: 'DELETE' })
      loadRepositories()
    } finally {
      setDeletingId(null)
    }
  }

  const handleReanalyze = async (id: number) => {
    setAnalyzingId(id)
    setExpandedCategory(null)
    try {
      const response = await apiFetch(`/repositories/${id}/analyze`, { method: 'POST' })
      if (!response.ok) {
        const data = await response.json()
        setError(data.detail)
        return
      }
      setActiveRepositoryId(id)
      await loadRepositories()
    } finally {
      setAnalyzingId(null)
    }
  }

  const addAndAnalyze = async (targetUrl: string) => {
    const createResponse = await apiFetch('/repositories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: targetUrl }),
    })

    let repositoryId: number
    if (createResponse.status === 409) {
      const allRepos = await loadRepositories()
      const existing = allRepos.find((candidate) => candidate.url === targetUrl)
      if (!existing) {
        setError('Repository already exists but could not be located.')
        return
      }
      repositoryId = existing.id
    } else if (!createResponse.ok) {
      const data = await createResponse.json()
      setError(data.detail)
      return
    } else {
      repositoryId = (await createResponse.json()).id
    }

    const analyzeResponse = await apiFetch(`/repositories/${repositoryId}/analyze`, {
      method: 'POST',
    })

    if (!analyzeResponse.ok) {
      const data = await analyzeResponse.json()
      setError(data.detail)
      return
    }

    setActiveRepositoryId(repositoryId)
    setExpandedCategory(null)
    await loadRepositories()
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setGithubRepos([])

    const trimmed = query.trim()
    if (!trimmed) return

    setIsSubmitting(true)
    try {
      if (GITHUB_REPO_URL_PATTERN.test(trimmed)) {
        await addAndAnalyze(trimmed)
      } else {
        const response = await apiFetch(`/github/${trimmed}/repos`)
        if (!response.ok) {
          const data = await response.json()
          setError(data.detail)
          return
        }
        setGithubRepos(await response.json())
      }
    } catch {
      setError('Could not reach the backend server. Is it running?')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSelectRepo = async (repo: GithubRepoSummary) => {
    setSelectingUrl(repo.html_url)
    setError(null)
    try {
      await addAndAnalyze(repo.html_url)
    } catch {
      setError('Could not reach the backend server. Is it running?')
    } finally {
      setSelectingUrl(null)
    }
  }

  const activeRepository = repositories.find((repository) => repository.id === activeRepositoryId)
  const activeReport = activeRepository?.analysis_report ?? null

  return (
    <div className="app">
      <header className="app-header">
        <h1>DevProof</h1>
        <p className="tagline">Evidence-based GitHub repository analysis</p>
        {currentUser && (
          <div className="auth-bar">
            {currentUser.avatar_url && (
              <img className="avatar" src={currentUser.avatar_url} alt={currentUser.github_username} />
            )}
            <span>{currentUser.github_username}</span>
            <button className="btn btn-small" onClick={handleLogout}>
              Log out
            </button>
          </div>
        )}
      </header>

      {checkingAuth ? null : !currentUser ? (
        <section className="card">
          <h2>Sign in to get started</h2>
          <button
            className="btn btn-primary"
            onClick={() => {
              window.location.href = `${API_BASE}/auth/github/login`
            }}
          >
            Sign in with GitHub
          </button>
        </section>
      ) : (
        <>
      <section className="card">
        <h2>Analyze a GitHub repository</h2>
        <form className="inline-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="GitHub username or repository URL"
            disabled={isSubmitting}
          />
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Working...' : 'Analyze'}
          </button>
        </form>
        {error && <p className="error-text">{error}</p>}

        {githubRepos.length > 0 && (
          <ul className="repo-picker-list">
            {githubRepos.map((repo) => (
              <li key={repo.full_name} className="repo-picker-item">
                <div className="repo-picker-info">
                  <span className="repo-name">{repo.full_name}</span>
                  <span className="repo-meta">
                    ★ {repo.stargazers_count} · {repo.language ?? 'unknown language'}
                  </span>
                </div>
                <button
                  className="btn btn-secondary"
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
        <section className="card report-card">
          <h2>Engineering Readiness Report</h2>
          <p className="report-subject">{activeRepository?.url}</p>

          <div className="overall-score">
            <ScoreBadge score={activeReport.overall_score} />
            <span className="overall-score-label">Overall Score</span>
          </div>

          <h3>Categories</h3>
          <p className="category-hint">Click a category for the full explanation.</p>
          <ul className="category-list">
            {activeReport.categories.map((category) => {
              const isExpanded = expandedCategory === category.name
              return (
                <li key={category.name} className="category-item-wrapper">
                  <button
                    type="button"
                    className={`category-item${isExpanded ? ' category-item-expanded' : ''}`}
                    onClick={() => setExpandedCategory(isExpanded ? null : category.name)}
                    aria-expanded={isExpanded}
                  >
                    <ScoreBadge score={category.score} />
                    <div className="category-text">
                      <div className="category-name">{category.name}</div>
                      <div className="category-comment">{category.comment}</div>
                    </div>
                    <span className="category-chevron">{isExpanded ? '▲' : '▼'}</span>
                  </button>
                  {isExpanded && (
                    <div className="category-details">{category.details}</div>
                  )}
                </li>
              )
            })}
          </ul>

          <div className="report-columns">
            <div>
              <h3>Strengths</h3>
              <ul className="plain-list">
                {activeReport.strengths.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div>
              <h3>Weaknesses</h3>
              <ul className="plain-list">
                {activeReport.weaknesses.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </div>

          <h3>Recommendations</h3>
          <ul className="plain-list">
            {activeReport.recommendations.map((item) => <li key={item}>{item}</li>)}
          </ul>

          <h3>Learning Roadmap</h3>
          <ul className="plain-list">
            {activeReport.learning_roadmap.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
      )}

      <section className="card">
        <h2>Previously Analyzed Repositories</h2>

        <div className="table-scroll">
        <table className="repo-table">
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
                <td>
                  {repository.credibility_score !== null
                    ? <ScoreBadge score={repository.credibility_score} />
                    : '-'}
                </td>
                <td className="row-actions">
                  <button
                    className="btn btn-small"
                    onClick={() => handleFetch(repository.id)}
                    disabled={fetchingId === repository.id || deletingId === repository.id || analyzingId === repository.id}
                  >
                    {fetchingId === repository.id ? 'Fetching...' : 'Fetch'}
                  </button>
                  <button
                    className="btn btn-small btn-secondary"
                    onClick={() => handleReanalyze(repository.id)}
                    disabled={fetchingId === repository.id || deletingId === repository.id || analyzingId === repository.id}
                  >
                    {analyzingId === repository.id
                      ? 'Analyzing...'
                      : repository.analysis_report
                        ? 'Re-analyze'
                        : 'Analyze'}
                  </button>
                  <button
                    className="btn btn-small btn-danger"
                    onClick={() => handleDelete(repository.id)}
                    disabled={fetchingId === repository.id || deletingId === repository.id || analyzingId === repository.id}
                  >
                    {deletingId === repository.id ? 'Deleting...' : 'Delete'}
                  </button>
                  {repository.analysis_report && (
                    <button
                      className="btn btn-small btn-secondary"
                      onClick={() => {
                        setActiveRepositoryId(repository.id)
                        setExpandedCategory(null)
                      }}
                    >
                      View Report
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </section>
        </>
      )}
    </div>
  )
}

export default App
