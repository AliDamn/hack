import { useEffect, useRef, useState } from 'react'
import { analyzeCase, getCase, listCases } from './api'
import './rulebook.css'

const STEP_MS = 700
const DEFAULT_STEPS = [
  'Classifying dispute type...',
  'Matching transactions...',
  'Checking network rules...',
  'Calculating risk score...',
  'Generating decision...',
]

const Arrow = () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M5 12L19 12M13 18L19 12M13 6L19 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
const Chk = ({ c }) => <svg width="24" height="25" viewBox="0 0 24 25" fill="none"><path d="M5 12.67L10 17.67L20 7.67" stroke={c} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>

function Demo() {
  const [cases, setCases] = useState([])
  const [sel, setSel] = useState(null)
  const [c, setC] = useState(null)
  const [phase, setPhase] = useState('idle')
  const [step, setStep] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const timer = useRef(null)

  useEffect(() => {
    listCases().then(setCases).catch((e) => setError(e.message))
    return () => clearInterval(timer.current)
  }, [])

  async function pick(i) {
    clearInterval(timer.current)
    setSel(i); setPhase('idle'); setStep(0); setResult(null); setError(null)
    try { setC(await getCase(cases[i].id)) } catch (e) { setC(null); setError(e.message) }
  }

  function analyze() {
    const caseId = c.id
    setPhase('loading'); setStep(0); setError(null)
    // Same 5 x 700ms progress animation as the original; the API call runs in parallel.
    const animation = new Promise((resolve) => {
      let s = 0
      timer.current = setInterval(() => {
        s++; setStep(s)
        if (s >= 5) { clearInterval(timer.current); resolve() }
      }, STEP_MS)
    })
    Promise.all([analyzeCase(caseId), animation])
      .then(([decision]) => { setResult(decision); setPhase('done') })
      .catch((e) => { clearInterval(timer.current); setError(e.message); setPhase('idle') })
  }

  const steps = result?.steps ?? DEFAULT_STEPS

  return <section style={{background:'var(--t-bg)'}} id="demo"><div className="t-demo">
    <div className="t-label t-label-muted" style={{marginBottom:'16px'}}>Live Preview</div>
    <h2 style={{fontSize:'45px',fontWeight:500,lineHeight:'110%',color:'var(--t-ink)',marginBottom:'8px'}}>Try the Engine</h2>
    <div style={{color:'var(--t-text-body)'}}>Select a dispute case. AI classifies, matches transactions, generates a decision.</div>
    <div className="t-demo-box">
      <div className="t-chips" role="group" aria-label="Cases">{cases.map((cs, i) => <button key={cs.id} className={'t-chip' + (sel === i ? ' active' : '')} onClick={() => pick(i)} type="button" aria-pressed={sel === i}>{cs.chip}</button>)}</div>
      {error && <div className="t-error" role="alert">{error}</div>}
      {c && <div>
        <div className="t-response-field"><div className="t-response-fl">Complaint — {c.id}</div><div className="t-response-fv" style={{color:'var(--t-ink)'}}>{c.complaint}</div></div>
        <div style={{marginTop:'16px'}}><div className="t-response-fl" style={{marginBottom:'8px'}}>Transactions</div>
          {c.transactions.map((t, i) => <div key={i} style={{display:'flex',justifyContent:'space-between',padding:'8px 0',borderBottom:'1px solid var(--t-border-dark)',fontSize:'14px',flexWrap:'wrap',gap:'8px'}}>
            <span style={{color:'var(--t-ink)'}}>{t.merchant}</span>
            <span style={{display:'flex',gap:'16px',color:'var(--t-text-muted)'}}><span>{t.amount}</span><span>{t.date}</span><span>{t.auth}</span></span>
          </div>)}
        </div>
        {phase === 'idle' && <div style={{marginTop:'20px'}}><button className="t-btn t-btn-light" onClick={analyze} type="button">Analyze Dispute <Arrow/></button></div>}
        {phase === 'loading' && <div className="t-loading" role="status"><div className="t-spinner"/>{steps[step < 5 ? step : 4]}</div>}
        {phase === 'done' && result && <div className="t-response" role="region" aria-live="polite">
          <div className="t-response-label">ClaimAI Decision · Confidence {result.confidence}%</div>
          <div className="t-response-field"><div className="t-response-fl">Type</div><div className="t-response-fv">{result.type}</div></div>
          <div className="t-response-field"><div className="t-response-fl">Decision</div><div className="t-response-fv"><span className={'t-decision-badge t-badge-' + result.decision_class}>{result.decision}</span></div></div>
          <div className="t-response-field"><div className="t-response-fl">Risk</div><div className="t-response-fv"><strong>{result.risk}/100</strong></div></div>
          <div className="t-response-field"><div className="t-response-fl">Reasoning</div><div className="t-response-fv">{result.reasoning}</div></div>
          <div className="t-response-field"><div className="t-response-fl">Actions</div><div className="t-response-fv">{result.actions.map((a, i) => <div key={i}>{'• ' + a}</div>)}</div></div>
          <div className="t-letter-box">{result.letter}</div>
        </div>}
      </div>}
    </div>
  </div></section>
}

export default function App() {
  return <div className="t-page">
    <nav className="t-nav" role="navigation" aria-label="Main"><a href="/" className="t-nav-logo">Claim<em>AI</em></a><div className="t-nav-links"><a href="#demo">Demo</a><span className="t-nav-dot" aria-hidden="true"/><a href="#protocol">Protocol</a><span className="t-nav-dot" aria-hidden="true"/><a href="#contact">Contact</a></div></nav>

    <section style={{padding:'0 24px',background:'var(--t-bg)',position:'relative',overflow:'hidden'}}>
      <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:0.08,pointerEvents:'none'}} viewBox="0 0 1440 876" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="hg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="var(--t-hero-blue)" stopOpacity="0.5"/><stop offset="100%" stopColor="var(--t-hero-blue)" stopOpacity="0"/></linearGradient></defs><path d="M0 400Q360 200 720 400T1440 400" fill="none" stroke="url(#hg)" strokeWidth="1"/><path d="M0 450Q360 250 720 450T1440 450" fill="none" stroke="url(#hg)" strokeWidth="0.7"/><path d="M0 500Q360 300 720 500T1440 500" fill="none" stroke="url(#hg)" strokeWidth="0.5"/><circle cx="350" cy="350" r="200" fill="none" stroke="url(#hg)" strokeWidth="0.3"/></svg>
      <div className="t-hero"><div className="t-hero-content">
        <h1>Card Disputes.<br/><em>Automated.</em></h1>
        <div className="t-hero-sub"><strong>AI-powered dispute resolution for banks.</strong><br/><br/>From 5 days to 5 minutes. Operators handle 50 cases per day instead of 8 — with full compliance and audit trail.</div>
        <div><a href="#demo" className="t-btn t-btn-light">Try Live Demo <Arrow/></a></div>
      </div></div>
    </section>

    <section className="t-white" id="discover"><div className="t-white-inner">
      <div className="t-split" style={{marginBottom:'128px'}}>
        <div className="t-split-text">
          <h2>For Operations Teams</h2>
          <div className="t-desc">Customer complaint to decision in minutes. AI classifies, matches transactions, applies rules.</div>
          <div className="t-checks">
            <div className="t-check t-check-blue"><Chk c="var(--t-text-blue)"/>NLP intake — customer describes problem naturally</div>
            <div className="t-check t-check-blue"><Chk c="var(--t-text-blue)"/>Auto-matching with transaction data from processing</div>
            <div className="t-check t-check-blue"><Chk c="var(--t-text-blue)"/>Decision with reasoning — operator confirms in one click</div>
          </div>
          <div><a href="#protocol" className="t-btn t-btn-dark">Discover More <Arrow/></a></div>
        </div>
        <div className="t-split-img t-img-blue"><svg viewBox="0 0 400 400" style={{width:'80%',opacity:0.5}} aria-hidden="true"><defs><linearGradient id="v1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stopColor="var(--t-text-blue)" stopOpacity="0.4"/><stop offset="100%" stopColor="var(--t-text-blue)" stopOpacity="0.05"/></linearGradient></defs><rect x="40" y="60" width="320" height="36" rx="4" fill="url(#v1)"/><rect x="40" y="110" width="280" height="28" rx="4" fill="url(#v1)" opacity="0.6"/><rect x="40" y="150" width="300" height="28" rx="4" fill="url(#v1)" opacity="0.4"/><rect x="40" y="250" width="120" height="40" rx="20" fill="var(--t-text-blue)" opacity="0.15"/></svg></div>
      </div>
      <div className="t-split t-split-rev">
        <div className="t-split-text">
          <h2>For Compliance Officers</h2>
          <div className="t-desc">Every decision traceable. Full audit trail. Human-in-the-loop — AI recommends, operator confirms.</div>
          <div className="t-checks">
            <div className="t-check t-check-green"><Chk c="var(--t-text-green)"/>Decision grounded in payment network rules</div>
            <div className="t-check t-check-green"><Chk c="var(--t-text-green)"/>Audit log with operator ID, timestamp, reasoning</div>
            <div className="t-check t-check-green"><Chk c="var(--t-text-green)"/>On-premise — customer PII never leaves your infra</div>
          </div>
          <div><a href="#protocol" className="t-btn t-btn-dark">Discover More <Arrow/></a></div>
        </div>
        <div className="t-split-img t-img-green"><svg viewBox="0 0 400 400" style={{width:'80%',opacity:0.5}} aria-hidden="true"><path d="M60 340L60 220L160 220L160 150L260 150L260 80L340 80" fill="none" stroke="var(--t-text-green)" strokeWidth="1.5" opacity="0.5"/><circle cx="60" cy="340" r="5" fill="var(--t-text-green)" opacity="0.6"/><circle cx="160" cy="220" r="5" fill="var(--t-text-green)" opacity="0.6"/><circle cx="260" cy="150" r="5" fill="var(--t-text-green)" opacity="0.6"/><circle cx="340" cy="80" r="5" fill="var(--t-text-green)" opacity="0.6"/></svg></div>
      </div>
    </div></section>

    <section className="t-vision"><div className="t-vision-inner">
      <div className="t-label t-label-muted">Vision</div>
      <h2>Every card dispute resolved instantly, transparently, and free of manual bottlenecks.</h2>
      <div><a href="#demo" className="t-btn t-btn-light">Try the engine <Arrow/></a></div>
    </div></section>

    <section className="t-white" id="protocol"><div className="t-white-inner"><div className="t-proto">
      <div className="t-proto-header"><div className="t-label t-label-blue">How It Works</div><h2>The ClaimAI <em>Protocol</em></h2><div className="t-proto-desc">From customer complaint to resolution — four stages, fully automated, operator confirms.</div></div>
      <div className="t-features">
        <div className="t-features-row"><div className="t-feature"><h3>NLP Intake</h3><p>Customer describes the problem naturally. LLM extracts dispute type, amount, merchant, timeframe automatically.</p></div><div className="t-feature"><h3>Transaction Matching</h3><p>System queries processing center, finds matching transactions by amount, date, merchant. Cross-references card activity.</p></div></div>
        <div className="t-features-row"><div className="t-feature"><h3>Decision Engine</h3><p>LLM applies payment network rules, bank policy, and fraud signals. Generates decision with confidence score and reasoning.</p></div><div className="t-feature"><h3>Letter Generation</h3><p>Auto-generates customer notification with case number, decision, next steps. Operator reviews and sends in one click.</p></div></div>
      </div>
    </div></div></section>

    <section className="t-dark"><div className="t-dark-inner">
      <div style={{display:'flex',flexDirection:'column',gap:'16px'}}><div className="t-label t-label-muted">Architecture</div><h2>Three Layers of <em>Intelligence</em></h2><div className="t-desc" style={{color:'var(--t-ink)',fontSize:'24px',lineHeight:'32px'}}>Every dispute passes through classification, verification, and compliance.</div></div>
      <div className="t-tranches">
        <div className="t-tranche"><div className="t-tranche-title t-tranche-green">Classification</div><p>NLP classifies dispute type: unauthorized fraud, ATM non-dispensation, duplicate charge, merchandise issue, recurring cancel.</p></div>
        <div className="t-tranche"><div className="t-tranche-title t-tranche-blue">Verification</div><p>Cross-references transaction data: 3D-Secure status, auth method, merchant location, card activity pattern. Risk score.</p></div>
        <div className="t-tranche"><div className="t-tranche-title t-tranche-orange">Compliance</div><p>Applies payment network chargeback rules, checks timeframes, generates audit-ready reasoning with rule references.</p></div>
      </div>
    </div></section>

    <Demo/>

    <section style={{background:'var(--t-bg)',position:'relative',overflow:'hidden'}} id="contact">
      <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:0.06,pointerEvents:'none'}} viewBox="0 0 1440 820" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><defs><linearGradient id="bg2" x1="100%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stopColor="var(--t-hero-blue)" stopOpacity="0.3"/><stop offset="100%" stopColor="var(--t-hero-blue)" stopOpacity="0"/></linearGradient></defs><path d="M0 450Q360 650 720 450T1440 450" fill="none" stroke="url(#bg2)" strokeWidth="1"/><path d="M0 400Q360 600 720 400T1440 400" fill="none" stroke="url(#bg2)" strokeWidth="0.6"/></svg>
      <div className="t-cta-bottom"><div className="t-cta-bottom-inner">
        <h2>Automate disputes. Not compliance.</h2>
        <div className="t-cta-btns"><a href="mailto:hello@claimai.kz" className="t-btn t-btn-light">Speak to our Team <Arrow/></a><a href="#demo" className="t-btn t-btn-light">Try Live Demo <Arrow/></a></div>
      </div></div>
    </section>

    <footer className="t-footer" role="contentinfo"><span>ClaimAI 2026 · AI for Finance Track</span></footer>
  </div>
}
