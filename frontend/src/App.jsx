import React, { useState, useEffect } from 'react';
import axios from 'axios';
import PRViewer from './components/PRViewer';
import './App.css';

const API_BASE_URL = "http://localhost:8001/api/v1";

/* ─── small reusable pieces ─── */

function StageBadge({ status }) {
  const map = {
    READY: { color: 'var(--text-muted)', bg: 'rgba(48, 74, 98, 0.15)', border: 'rgba(48, 74, 98, 0.3)' },
    STANDBY: { color: 'var(--text-muted)', bg: 'rgba(48, 74, 98, 0.15)', border: 'rgba(48, 74, 98, 0.3)' },
    INDEXING: { color: 'var(--cyan)', bg: 'var(--cyan-dim)', border: 'rgba(0,200,255,0.25)' },
    INDEXED: { color: 'var(--green)', bg: 'var(--green-dim)', border: 'rgba(0,232,122,0.28)' },
    RUNNING: { color: 'var(--cyan)', bg: 'var(--cyan-dim)', border: 'rgba(0,200,255,0.25)' },
    COMPLETE: { color: 'var(--green)', bg: 'var(--green-dim)', border: 'rgba(0,232,122,0.28)' },
  };
  const s = map[status] || map.READY;
  return (
    <span className="stage-badge" style={{ color: s.color, background: s.bg, borderColor: s.border }}>
      {(status === 'RUNNING' || status === 'INDEXING') && '◌ '}
      {status}
    </span>
  );
}

function StageHeader({ num, label, status }) {
  return (
    <div className="stage-header">
      <span className="stage-num">{String(num).padStart(2, '0')}</span>
      <h2 className="stage-label">{label}</h2>
      <StageBadge status={status} />
    </div>
  );
}

function SevBadge({ type }) {
  const cls = type === 'CRITICAL' ? 'critical' : type === 'WARNING' ? 'warning' : 'note';
  const label = type === 'CRITICAL' ? '● CRITICAL' : type === 'WARNING' ? '◆ WARNING' : '◉ NOTE';
  return <span className={`sev-badge ${cls}`}>{label}</span>;
}

/* ─── loading pipeline steps ─── */
const STEPS = [
  'fetching diff',
  'embedding chunks',
  'querying memory',
  'generating review',
];

function PipelineLoader() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setActive(prev => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 1800);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="pipeline-loading">
      <span className="loading-label">RagView running</span>
      <div className="pipeline-steps">
        {STEPS.map((step, i) => (
          <React.Fragment key={step}>
            <div className={`pipeline-step${i <= active ? ' is-active' : ''}`}>
              <span className="step-orb"></span>
              <span>{step}</span>
            </div>
            {i < STEPS.length - 1 && <span className="step-connector">─</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}

/* ─── main app ─── */

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('rag-theme') || 'dark');
  const [prUrl, setPrUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [review, setReview] = useState(null);
  const [error, setError] = useState(null);

  const [ingestRepo, setIngestRepo] = useState('');
  const [ingestLimit, setIngestLimit] = useState(10);
  const [ingesting, setIngesting] = useState(false);
  const [ingestMsg, setIngestMsg] = useState(null);

  const [memoryData, setMemoryData] = useState(null);
  const [loadingMem, setLoadingMem] = useState(false);

  /* derived stage statuses */
  const ingestStatus = ingesting ? 'INDEXING' : ingestMsg ? 'INDEXED' : 'READY';
  const reviewStatus = loading ? 'RUNNING' : review ? 'COMPLETE' : 'STANDBY';

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('rag-theme', theme);
  }, [theme]);

  const handleReview = async () => {
    if (!prUrl) return;
    setLoading(true);
    setError(null);
    setReview(null);
    setIngestMsg(null);
    setMemoryData(null);
    try {
      const res = await axios.post(`${API_BASE_URL}/reviews/analyze`, { pr_url: prUrl });
      setReview(res.data);
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Failed to fetch review. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    if (!ingestRepo) return;
    setIngesting(true);
    setError(null);
    setIngestMsg(null);
    setMemoryData(null);
    try {
      const res = await axios.post(`${API_BASE_URL}/reviews/ingest-history`, {
        repo_url: ingestRepo,
        limit: parseInt(ingestLimit),
      });
      setIngestMsg(res.data.message);
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Failed to trigger ingestion pipeline.');
    } finally {
      setIngesting(false);
    }
  };

  const toggleMemory = async () => {
    if (memoryData) { setMemoryData(null); return; }
    setLoadingMem(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/reviews/memory`);
      setMemoryData(res.data);
    } catch {
      setError('Failed to fetch memory from ChromaDB.');
    } finally {
      setLoadingMem(false);
    }
  };

  return (
    <div className="app-shell">

      {/* ── top nav ── */}
      <nav className="top-nav">
        <div className="nav-brand">
          <div className="brand-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="brand-name">RAGVIEW</span>
          <span className="brand-divider">/</span>
          <span className="brand-sub">rag-powered code reviewer</span>
        </div>
        <div className="nav-status">
          <button
            className="btn-ghost"
            style={{ padding: '0.2rem 0.5rem', marginRight: '0.5rem' }}
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
          >
            {theme === 'dark' ? '☀ LIGHT' : '☾ DARK'}
          </button>
          <div className="status-pill"><span className="status-dot cyan" /><span>vector store</span></div>
          <div className="status-pill"><span className="status-dot green" /><span>llm pipeline</span></div>
          <div className="status-pill"><span className="status-dot amber" /><span>github api</span></div>
        </div>
      </nav>

      {/* ── main content ── */}
      <div className="content-wrapper">

        {/* hero */}
        <header className="hero-section">
          <div className="hero-eyebrow">// context-aware pull request intelligence</div>
          <h1 className="hero-title">
            <span className="title-rag">RAG</span>
            <span className="title-sep">—</span>
            <span className="title-main">CODE REVIEWER</span>
          </h1>
          <p className="hero-desc">
            Analyze pull requests grounded in your team's historical code decisions,
            patterns, and merged PR review history — powered by LangChain + ChromaDB.
          </p>
        </header>

        {/* error */}
        {error && (
          <div className="alert alert-error">
            <span className="alert-icon">⚠</span>
            <span>{error}</span>
            <button className="alert-dismiss" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {/* ─── stage 01: ingest ─── */}
        <section className="pipeline-card">
          <StageHeader num={1} label="BUILD RAG MEMORY" status={ingestStatus} />
          <div className="card-body">
            <p className="card-desc">
              Scrape merged pull requests from a GitHub repository to populate the vector
              memory. This context grounds every subsequent code review in real team history.
            </p>

            <div className="input-row">
              <div className="field" style={{ flex: 3 }}>
                <label className="field-label">REPOSITORY URL</label>
                <input
                  type="text"
                  value={ingestRepo}
                  onChange={e => setIngestRepo(e.target.value)}
                  placeholder="owner/repo  or  https://github.com/owner/repo"
                  className="rag-input"
                />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label className="field-label">PR LIMIT</label>
                <input
                  type="number"
                  value={ingestLimit}
                  onChange={e => setIngestLimit(e.target.value)}
                  placeholder="10"
                  className="rag-input"
                />
              </div>
              <div className="field" style={{ minWidth: 150 }}>
                <label className="field-label">&nbsp;</label>
                <button onClick={handleIngest} disabled={ingesting || !ingestRepo} className="btn btn-green">
                  {ingesting
                    ? <><span className="btn-spinner" />&nbsp;INDEXING...</>
                    : <>▶ &nbsp;RUN INGEST</>}
                </button>
              </div>
            </div>

            {ingestMsg && (
              <div className="alert alert-success">
                <span className="alert-icon">✓</span>
                <span>{ingestMsg}</span>
              </div>
            )}

            <div className="memory-row">
              <button onClick={toggleMemory} disabled={loadingMem} className="btn-ghost">
                {loadingMem ? '◌ loading...' : memoryData ? '◉ hide memory db' : '◎ inspect memory db'}
              </button>
            </div>

            {memoryData && (
              <div className="terminal-box">
                <div className="terminal-bar">
                  <div className="terminal-traffic"><span /><span /><span /></div>
                  <span className="terminal-title">chromadb — {memoryData.count} vectors indexed</span>
                </div>
                <pre className="terminal-body">{JSON.stringify(memoryData.data, null, 2)}</pre>
              </div>
            )}
          </div>
        </section>

        {/* ─── stage 02: review ─── */}
        <section className="pipeline-card">
          <StageHeader num={2} label="ANALYZE PULL REQUEST" status={reviewStatus} />
          <div className="card-body">
            <p className="card-desc">
              Paste any GitHub Pull Request URL. The RAG pipeline will fetch the diff,
              retrieve similar historical reviews from memory, and generate contextual feedback.
            </p>

            <div className="input-row">
              <div className="field" style={{ flex: 1 }}>
                <label className="field-label">PULL REQUEST URL</label>
                <input
                  type="text"
                  value={prUrl}
                  onChange={e => setPrUrl(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleReview()}
                  placeholder="https://github.com/owner/repo/pull/123"
                  className="rag-input"
                />
              </div>
              <div className="field" style={{ minWidth: 160 }}>
                <label className="field-label">&nbsp;</label>
                <button onClick={handleReview} disabled={loading || !prUrl} className="btn btn-cyan">
                  {loading
                    ? <><span className="btn-spinner" />&nbsp;ANALYZING...</>
                    : <>▶ &nbsp;ANALYZE PR</>}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* loading */}
        {loading && <PipelineLoader />}

        {/* empty */}
        {!review && !loading && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="0.9">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
                <path d="M8 11h6M11 8v6" />
              </svg>
            </div>
            <p>Awaiting pull request URL to begin analysis</p>
            <span>Stage 01 is optional — you can paste a PR URL and analyze immediately</span>
          </div>
        )}

        {/* ─── results ─── */}
        {review?.files && (
          <div className="results-wrap">

            {review.summary && (
              <div className="summary-card">
                <div className="summary-header">
                  <span className="summary-tag">PR SUMMARY</span>
                  <span className="summary-count">{review.files.length} FILES REVIEWED</span>
                </div>
                <div className="summary-body">{review.summary}</div>
              </div>
            )}

            {review.files.map((file, idx) => {
              const fileReviews = review.reviews.filter(r => r.file === file.filename);
              const criticalCount = fileReviews.filter(r => r.type === 'CRITICAL').length;
              const warningCount = fileReviews.filter(r => r.type === 'WARNING').length;

              return (
                <div key={idx} className="file-card">

                  {/* file header */}
                  <div className="file-card-header">
                    <div className="file-path-wrap">
                      <span className="file-idx">[{String(idx + 1).padStart(2, '0')}]</span>
                      <span className="file-path">{file.filename}</span>
                    </div>
                    <div className="file-badges">
                      {criticalCount > 0 && <span className="file-badge critical">{criticalCount} CRITICAL</span>}
                      {warningCount > 0 && <span className="file-badge warning">{warningCount} WARNING</span>}
                      {fileReviews.length === 0 && <span className="file-badge clean">✓ CLEAN</span>}
                    </div>
                  </div>

                  {/* diff + feedback grid */}
                  <div className="review-grid">

                    {/* diff panel */}
                    <div className="diff-panel">
                      <div className="panel-head">DIFF VIEW</div>
                      <PRViewer
                        originalCode={file.original_code}
                        modifiedCode={file.modified_code}
                        language="python"
                      />
                    </div>

                    {/* feedback panel */}
                    <div className="feedback-panel">
                      <div className="panel-head">
                        AI FEEDBACK &mdash; {fileReviews.length} COMMENT{fileReviews.length !== 1 ? 'S' : ''}
                      </div>
                      <div className="feedback-scroll">
                        {fileReviews.length === 0 ? (
                          <div className="feedback-clean">
                            <div className="clean-ico">✓</div>
                            <p>No issues detected</p>
                            <span>Code follows established patterns</span>
                          </div>
                        ) : (
                          fileReviews.map((item, i) => {
                            const cls = item.type === 'CRITICAL' ? 'is-critical'
                              : item.type === 'WARNING' ? 'is-warning'
                                : 'is-note';
                            return (
                              <div key={i} className={`feedback-item ${cls}`}>
                                <div className="feedback-meta">
                                  <SevBadge type={item.type} />
                                  <code className="feedback-line">:{item.line}</code>
                                </div>
                                <p className="feedback-msg">{item.message}</p>
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        )}

      </div>{/* end content-wrapper */}

      {/* footer */}
      <footer className="app-footer">
        <span>RAG Code Reviewer</span>
        <span>LangChain · ChromaDB · Google GenAI · FastAPI · React</span>
      </footer>

    </div>
  );
}

export default App;