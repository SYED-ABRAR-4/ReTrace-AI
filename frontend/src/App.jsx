import { useMemo, useState } from 'react'
import './App.css'

const analysisStages = [
  'Reading repository',
  'Finding relevant history',
  'Collecting evidence',
  'Reconstructing decision',
  'Building timeline',
]

const defaultRepo = 'https://github.com/microsoft/vscode'
const defaultQuestion = 'Why was this implemented this way?'

function App() {
  const [repoUrl, setRepoUrl] = useState(defaultRepo)
  const [question, setQuestion] = useState(defaultQuestion)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentStage, setCurrentStage] = useState(0)

  const confidenceLabel = useMemo(() => {
    if (!result) return 'High'
    return result.confidence.charAt(0).toUpperCase() + result.confidence.slice(1)
  }, [result])

  const handleAnalyze = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    const steps = analysisStages.map((_, index) => index)
    for (const stageIndex of steps) {
      setCurrentStage(stageIndex)
      await new Promise((resolve) => setTimeout(resolve, 220))
    }

    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl, question }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'The repository could not be analyzed.')
      }

      setResult(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setCurrentStage(0)
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Open-source reasoning engine</p>
          <h1>ReTrace AI</h1>
        </div>
        <span className="model-badge">Model: {result?.model_used || 'llama3.2:latest / local heuristic'}</span>
      </header>

      <main className="main-panel">
        <section className="input-panel">
          <p className="subtitle">Reconstruct the reasoning behind open-source code.</p>

          <form className="analyze-form" onSubmit={handleAnalyze}>
            <label>
              <span>GitHub Repository</span>
              <input
                type="url"
                value={repoUrl}
                onChange={(event) => setRepoUrl(event.target.value)}
                placeholder="https://github.com/owner/repository"
              />
            </label>

            <label>
              <span>Question</span>
              <textarea
                rows="4"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Why was this implemented this way?"
              />
            </label>

            <button type="submit" disabled={loading}>
              {loading ? 'Analyzing…' : 'ReTrace Decision'}
            </button>

            <p className="helper-text">
              ReTrace analyzes repository history and uses an open-weight AI model to reconstruct decisions from available evidence.
            </p>
          </form>

          {loading && (
            <div className="loading-panel" aria-live="polite">
              <div className="loader" />
              <div className="stage-list">
                {analysisStages.map((stage, index) => (
                  <div key={stage} className={`stage ${index === currentStage ? 'active' : ''}`}>
                    <span className="dot" />
                    {stage}
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && <div className="error-box">{error}</div>}
        </section>

        {result && (
          <section className="result-panel">
            <div className="result-header">
              <div>
                <p className="eyebrow">Decision Replay</p>
                <h2>Decision</h2>
              </div>
              <div className={`confidence-box ${result.confidence}`}>
                <span>Confidence</span>
                <strong>{confidenceLabel}</strong>
              </div>
            </div>

            <p className="confidence-note">
              Confidence reflects how strongly the available evidence supports the reconstruction.
            </p>

            <div className="decision-block">
              <p>{result.decision}</p>
            </div>

            <div className="section-grid">
              <article className="info-card">
                <h3>Facts</h3>
                <ul>
                  {result.facts.map((fact) => <li key={fact}>{fact}</li>)}
                </ul>
              </article>

              <article className="info-card">
                <h3>Inferences</h3>
                <ul>
                  {result.inferences.map((fact) => <li key={fact}>{fact}</li>)}
                </ul>
              </article>

              <article className="info-card">
                <h3>Unknown</h3>
                <ul>
                  {result.unknowns.map((fact) => <li key={fact}>{fact}</li>)}
                </ul>
              </article>
            </div>

            <div className="section-block">
              <h3>Evidence</h3>
              <div className="evidence-grid">
                {result.evidence.map((item) => (
                  <a key={`${item.title}-${item.link}`} href={item.link} target="_blank" rel="noreferrer" className="evidence-card">
                    <div className="chip-row">
                      <span className="chip source">{item.source_type}</span>
                      <span className="chip relevance">{item.relevance}</span>
                    </div>
                    <h4>{item.title}</h4>
                    <p>{item.excerpt}</p>
                    <small>{item.date}</small>
                  </a>
                ))}
              </div>
            </div>

            <div className="section-block">
              <h3>Decision Timeline</h3>
              <div className="timeline">
                {result.timeline.map((event, index) => (
                  <div key={`${event.stage}-${index}`} className="timeline-item">
                    <div className="timeline-line" />
                    <div className="timeline-content">
                      <span className="tag">{event.stage}</span>
                      <h4>{event.title}</h4>
                      <p>{event.description}</p>
                      <small>{event.date}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="meta-grid">
              <div className="meta-card">
                <h3>Current Impact</h3>
                <ul>
                  {result.affected_files.length ? (
                    result.affected_files.map((file) => <li key={file}>{file}</li>)
                  ) : (
                    <li>No affected files detected in the available public evidence.</li>
                  )}
                </ul>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
