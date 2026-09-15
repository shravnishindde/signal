import { useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const SAMPLE_LABELS = {
  deadline_conflict: 'Deadline conflict',
  scope_conflict: 'Scope conflict',
  no_conflict: 'No conflict (control)',
}

function SeverityDot({ severity }) {
  return <span className={`dot dot-${severity}`} aria-hidden="true" />
}

function ContradictionCard({ c }) {
  return (
    <div className={`card severity-${c.severity}`}>
      <div className="card-head">
        <SeverityDot severity={c.severity} />
        <span className="card-topic">{c.topic}</span>
        <span className="card-severity">{c.severity} severity</span>
      </div>
      <div className="claim-row">
        <span className="speaker">{c.speaker_a}</span>
        <span className="claim">"{c.claim_a}"</span>
      </div>
      <div className="claim-row">
        <span className="speaker">{c.speaker_b}</span>
        <span className="claim">"{c.claim_b}"</span>
      </div>
    </div>
  )
}

export default function App() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [samples, setSamples] = useState(null)

  async function loadSamples() {
    if (samples) return samples
    try {
      const res = await fetch(`${API_URL}/samples`)
      const data = await res.json()
      setSamples(data)
      return data
    } catch {
      return null
    }
  }

  async function useSample(key) {
    const data = samples || (await loadSamples())
    if (data && data[key]) {
      setText(data[key])
      setResult(null)
      setError(null)
    }
  }

  async function analyze() {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Request failed (${res.status})`)
      }
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setError(e.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div className="wordmark">
          <span className="wordmark-dot" />
          Signal
        </div>
        <p className="tagline">
          Other tools summarize what was said. Signal catches what doesn't add up.
        </p>
      </header>

      <main className="layout">
        <section className="panel input-panel">
          <label className="panel-label" htmlFor="thread">
            Paste a project thread
          </label>
          <textarea
            id="thread"
            className="thread-input"
            placeholder={`Priya (9:02 AM): Let's ship by Friday.\nRaj (11:42 AM): Confirming Monday works for everyone?`}
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={12}
          />

          <div className="sample-row">
            <span className="sample-row-label">Try an example</span>
            <div className="sample-buttons">
              {Object.keys(SAMPLE_LABELS).map((key) => (
                <button
                  key={key}
                  className="sample-btn"
                  onClick={() => useSample(key)}
                  type="button"
                >
                  {SAMPLE_LABELS[key]}
                </button>
              ))}
            </div>
          </div>

          <button
            className="scan-btn"
            onClick={analyze}
            disabled={loading || !text.trim()}
            type="button"
          >
            {loading ? 'Scanning…' : 'Scan thread'}
          </button>

          {loading && (
            <div className="scanline-track" aria-hidden="true">
              <div className="scanline" />
            </div>
          )}

          {error && <p className="error-text">{error}</p>}
        </section>

        <section className="panel results-panel">
          {!result && !loading && (
            <div className="empty-state">
              <p>Paste a thread and scan it.</p>
              <p className="empty-sub">
                Signal looks for two speakers making conflicting claims about the
                same deadline, scope, or ownership decision.
              </p>
            </div>
          )}

          {result && result.has_contradiction && (
            <div className="result-block">
              <div className="result-status status-conflict">
                <SeverityDot severity="high" />
                Contradiction detected — action triggered
              </div>

              {result.contradictions.map((c, i) => (
                <ContradictionCard key={i} c={c} />
              ))}

              <div className="triggered-action">
                <span className="triggered-label">Triggered clarification</span>
                <p className="triggered-message">{result.clarification_message}</p>
              </div>
            </div>
          )}

          {result && !result.has_contradiction && (
            <div className="result-block">
              <div className="result-status status-clear">
                <SeverityDot severity="clear" />
                No contradictions found
              </div>
              <p className="summary-text">{result.summary}</p>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
