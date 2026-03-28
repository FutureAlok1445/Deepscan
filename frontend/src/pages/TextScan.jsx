import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Sparkles, Shield, AlertCircle, Loader, Copy, Eraser,
  ChevronRight, Zap, Brain, CheckCircle, XCircle, HelpCircle,
} from 'lucide-react';
import gsap from 'gsap';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalButton from '../components/ui/BrutalButton';
import { analyzeText } from '../api/deepscan';

const SAMPLE_TEXTS = [
  {
    label: 'AI-Generated Sample',
    text: `Artificial intelligence has fundamentally transformed the landscape of modern technology, enabling unprecedented advancements across numerous domains. The integration of machine learning algorithms with natural language processing capabilities has created sophisticated systems that can analyze, interpret, and generate human-like text with remarkable accuracy. These developments have significant implications for industries ranging from healthcare to finance, where data-driven decision-making processes are becoming increasingly prevalent. Furthermore, the ethical considerations surrounding AI deployment continue to evolve, necessitating robust frameworks for responsible innovation and governance.`,
  },
  {
    label: 'Human-Written Sample',
    text: `I was walking home yesterday when I saw the strangest thing — a cat sitting on top of a mailbox, just staring at everyone who passed by. Made me laugh so hard I almost dropped my groceries. My neighbor Mrs. Patel said that cat's been doing it for weeks now. Nobody knows whose cat it is. Anyway, I finally got around to fixing that leaky faucet Dad's been bugging me about. Took way longer than I thought because I bought the wrong size washer the first time.`,
  },
];

const CHAR_LIMIT = 50000;
const MIN_WORDS = 5;

// Map backend verdicts to display config
function getVerdictConfig(verdict, score) {
  const v = (verdict || '').toLowerCase();
  if (v.includes('definitely') || v.includes('definite') || score >= 82) {
    return { label: verdict || 'Definitely AI', color: '#ff3c00', emoji: '🚨' };
  }
  if (v.includes('likely') || score >= 60) {
    return { label: verdict || 'Likely AI', color: '#ff8c00', emoji: '🔶' };
  }
  if (v.includes('uncertain') || v.includes('error') || (score >= 30 && score < 60)) {
    return { label: verdict || 'Uncertain', color: '#ffd700', emoji: '⚠️' };
  }
  return { label: verdict || 'Human Written', color: '#39ff14', emoji: '✅' };
}

export default function TextScan() {
  const [text, setText] = useState('');
  const [status, setStatus] = useState('idle'); // idle | analyzing | complete | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const pageRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.ts-header', { y: -30, opacity: 0, duration: 0.6, ease: 'power3.out' });
      gsap.from('.ts-input', { y: 20, opacity: 0, duration: 0.5, delay: 0.15, ease: 'power2.out' });
      gsap.from('.ts-actions', { y: 20, opacity: 0, duration: 0.5, delay: 0.3, ease: 'power2.out' });
    }, pageRef);
    return () => ctx.revert();
  }, []);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const handleAnalyze = useCallback(async () => {
    if (wordCount < MIN_WORDS) return;
    setStatus('analyzing');
    setError(null);
    setResult(null);
    try {
      const data = await analyzeText(text.trim());
      setResult(data);
      setStatus('complete');
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Analysis failed');
      setStatus('error');
    }
  }, [text, wordCount]);

  const handleReset = () => {
    setText('');
    setResult(null);
    setError(null);
    setStatus('idle');
  };

  const handlePaste = async () => {
    try {
      const clip = await navigator.clipboard.readText();
      if (clip) setText(clip);
    } catch {
      // clipboard access denied
    }
  };

  return (
    <div ref={pageRef} className="min-h-screen bg-ds-bg pt-20 sm:pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6 sm:space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center ts-header">
          <div className="inline-flex items-center gap-2 mb-3">
            <FileText className="w-5 h-5 text-ds-cyan animate-pulse" />
            <p className="text-xs font-mono text-ds-red uppercase tracking-[0.3em]">// TEXT SCAN</p>
            <Brain className="w-5 h-5 text-ds-yellow animate-pulse" />
          </div>
          <h1 className="text-2xl sm:text-3xl md:text-5xl font-grotesk font-black text-ds-silver">
            Detect <span className="text-ds-cyan drop-shadow-[0_0_20px_rgba(0,245,255,0.5)]">AI Text</span>
          </h1>
          <p className="mt-2 sm:mt-3 text-xs sm:text-sm font-mono text-ds-silver/50">
            Paste any text to check if it was written by ChatGPT, Claude, Gemini, or other AI
          </p>
        </div>

        {/* Sample Buttons */}
        <div className="flex flex-wrap gap-2 justify-center ts-input">
          {SAMPLE_TEXTS.map((s, i) => (
            <button
              key={i}
              onClick={() => { setText(s.text); setResult(null); setStatus('idle'); }}
              className="px-3 py-1.5 text-xs font-mono border-2 border-ds-silver/20 text-ds-silver/60 hover:border-ds-cyan hover:text-ds-cyan transition-all"
            >
              <Sparkles className="w-3 h-3 inline mr-1" />
              {s.label}
            </button>
          ))}
        </div>

        {/* Text Input */}
        <div className="ts-input">
          <BrutalCard hover={false} className="!p-0 overflow-hidden">
            <div className="flex items-center justify-between px-3 sm:px-4 py-2 border-b border-ds-silver/10 bg-ds-bg-alt/50">
              <span className="text-xs font-mono text-ds-silver/40">
                {wordCount} words · {charCount}/{CHAR_LIMIT} chars
              </span>
              <div className="flex gap-2">
                <button onClick={handlePaste} className="text-xs font-mono text-ds-silver/40 hover:text-ds-cyan flex items-center gap-1 transition-colors" title="Paste from clipboard">
                  <Copy className="w-3 h-3" /> Paste
                </button>
                {text && (
                  <button onClick={handleReset} className="text-xs font-mono text-ds-silver/40 hover:text-ds-red flex items-center gap-1 transition-colors" title="Clear">
                    <Eraser className="w-3 h-3" /> Clear
                  </button>
                )}
              </div>
            </div>
            <textarea
              value={text}
              onChange={(e) => { if (e.target.value.length <= CHAR_LIMIT) setText(e.target.value); }}
              placeholder={"Paste or type text here to analyze...\n\nMinimum 5 words required for accurate detection."}
              rows={8}
              className="w-full bg-transparent px-3 sm:px-4 py-3 font-mono text-sm text-ds-silver placeholder:text-ds-silver/20 focus:outline-none resize-y min-h-[160px] sm:min-h-[200px]"
              disabled={status === 'analyzing'}
            />
          </BrutalCard>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 p-3 sm:p-4 bg-ds-red/10 border-3 border-ds-red">
            <AlertCircle className="w-5 h-5 text-ds-red flex-shrink-0" />
            <p className="text-xs sm:text-sm font-mono text-ds-red">{error}</p>
          </div>
        )}

        {/* Analyze Button */}
        <div className="text-center ts-actions">
          <BrutalButton
            size="lg"
            onClick={handleAnalyze}
            disabled={wordCount < MIN_WORDS || status === 'analyzing'}
            className="group relative overflow-hidden"
          >
            {status === 'analyzing' ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Shield className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                <span>Scan Text</span>
                <Zap className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
              </>
            )}
          </BrutalButton>
          {wordCount > 0 && wordCount < MIN_WORDS && (
            <p className="mt-2 text-xs font-mono text-ds-yellow">Need at least {MIN_WORDS} words ({MIN_WORDS - wordCount} more)</p>
          )}
        </div>

        {/* Results */}
        {result && <TextResult result={result} />}
      </div>
    </div>
  );
}

/* ─── Result Display ─── */
function TextResult({ result }) {
  const sectionRef = useRef(null);
  // Handle both response shapes
  const score = result.overall_score ?? result.score ?? result.aacs_score ?? 0;
  const verdictConf = getVerdictConfig(result.verdict, score);
  const signals = result.details?.signals || {};
  const reasons = result.details?.reasons || [];
  const executionTime = result.execution_time ?? (result.processing_time_ms ? result.processing_time_ms / 1000 : 0);

  useEffect(() => {
    if (!sectionRef.current) return;
    const ctx = gsap.context(() => {
      gsap.from('.tr-card', { y: 30, opacity: 0, duration: 0.5, stagger: 0.1, ease: 'power2.out' });
    }, sectionRef);
    return () => ctx.revert();
  }, []);

  return (
    <div ref={sectionRef} className="space-y-4 sm:space-y-6">
      {/* Score Card */}
      <BrutalCard className="tr-card text-center !py-6 sm:!py-8">
        <div className="relative inline-block mb-3 sm:mb-4">
          <div className="relative w-40 h-40 sm:w-48 sm:h-48 flex items-center justify-center mx-auto">
            <svg className="w-full h-full transform -rotate-90">
              <circle cx="50%" cy="50%" r="45%" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
              <circle
                cx="50%" cy="50%" r="45%"
                fill="transparent"
                stroke={verdictConf.color}
                strokeWidth="8"
                strokeDasharray={`${(score / 100) * 283} 283`}
                strokeLinecap="round"
                style={{ transition: 'stroke-dasharray 1.5s ease-out' }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl sm:text-5xl font-grotesk font-black" style={{ color: verdictConf.color }}>
                {Math.round(score)}%
              </span>
              <span className="text-[10px] font-mono text-ds-silver/40 uppercase tracking-widest mt-1">
                AI Probability
              </span>
            </div>
          </div>
        </div>
        <div
          className="inline-flex items-center gap-2 px-4 py-2 border-3 font-grotesk font-bold text-sm sm:text-base uppercase"
          style={{ borderColor: verdictConf.color, color: verdictConf.color }}
        >
          {verdictConf.emoji} {verdictConf.label}
        </div>
        <div className="mt-3 flex flex-wrap justify-center gap-4 text-xs font-mono text-ds-silver/40">
          <span>{result.word_count || '—'} words</span>
          <span>{executionTime.toFixed(2)}s analysis</span>
        </div>
      </BrutalCard>

      {/* Signal Bars */}
      {Object.keys(signals).length > 0 && (
        <BrutalCard className="tr-card">
          <h3 className="font-grotesk font-bold text-base sm:text-lg text-ds-silver mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-ds-cyan" />
            Detection Signals
          </h3>
          <div className="space-y-4">
            {signals.hf_model != null && (
              <SignalBar label="Model Confidence" value={signals.hf_model} sub="Neural pattern matching" />
            )}
            {signals.perplexity != null && (
              <SignalBar label="Perplexity" value={Math.max(0, 100 - signals.perplexity / 2)} sub="Text predictability (lower = more AI-like)" />
            )}
            {signals.burstiness != null && (
              <SignalBar label="Burstiness" value={Math.max(0, 100 - signals.burstiness)} sub="Sentence variance (lower = more uniform = AI)" />
            )}
            {signals.sapling_api != null && (
              <SignalBar label="AI Consensus" value={signals.sapling_api} sub="Multi-engine LLM detection" />
            )}
          </div>
        </BrutalCard>
      )}

      {/* Forensic Insights */}
      {reasons.length > 0 && (
        <BrutalCard className="tr-card">
          <h3 className="font-grotesk font-bold text-base sm:text-lg text-ds-silver mb-3 flex items-center gap-2">
            <Brain className="w-4 h-4 sm:w-5 sm:h-5 text-ds-yellow" />
            Forensic Insights
          </h3>
          <ul className="space-y-2">
            {reasons.map((reason, idx) => (
              <li
                key={idx}
                className="flex items-center gap-3 text-xs sm:text-sm font-mono text-ds-silver/70"
              >
                <div className={`w-1.5 h-1.5 flex-shrink-0 ${score > 60 ? 'bg-ds-red' : score > 30 ? 'bg-ds-yellow' : 'bg-ds-green'}`} />
                {reason}
              </li>
            ))}
          </ul>
        </BrutalCard>
      )}

      {/* Sentence Breakdown (only if available) */}
      {result.sentence_scores?.length > 0 && (
        <BrutalCard className="tr-card">
          <h3 className="font-grotesk font-bold text-base sm:text-lg text-ds-silver mb-3 sm:mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-ds-cyan" />
            Sentence-Level Breakdown
          </h3>
          <div className="space-y-2 sm:space-y-3 max-h-80 overflow-y-auto pr-1 sm:pr-2">
            {result.sentence_scores.map((s, i) => (
              <SentenceRow key={i} sentence={s} index={i} />
            ))}
          </div>
        </BrutalCard>
      )}
    </div>
  );
}

function SignalBar({ label, value, sub }) {
  const normValue = Math.max(0, Math.min(100, value || 0));
  const color = normValue >= 70 ? '#ff3c00' : normValue >= 40 ? '#ffd700' : '#39ff14';

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-end">
        <div>
          <p className="text-sm font-bold font-grotesk text-ds-silver uppercase">{label}</p>
          <p className="text-[10px] font-mono text-ds-silver/30">{sub}</p>
        </div>
        <span className="text-xs font-mono font-bold" style={{ color }}>
          {Math.round(normValue)}%
        </span>
      </div>
      <div className="h-1.5 bg-ds-silver/5 border border-ds-silver/10">
        <div
          className="h-full transition-all duration-1000 ease-out"
          style={{ width: `${normValue}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function SentenceRow({ sentence, index }) {
  const prob = sentence.ai_probability ?? 50;
  const Icon = prob >= 60 ? XCircle : prob < 30 ? CheckCircle : HelpCircle;
  const color = prob >= 60 ? '#ff3c00' : prob < 30 ? '#39ff14' : '#ffd700';

  return (
    <div className="flex items-start gap-2 sm:gap-3 p-2 sm:p-3 bg-ds-bg-alt/50 border border-ds-silver/10">
      <div className="flex-shrink-0 mt-0.5">
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs sm:text-sm font-mono text-ds-silver/80 break-words">{sentence.text}</p>
        <div className="flex items-center gap-2 mt-1.5">
          <div className="flex-1 h-1.5 bg-ds-silver/10 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{ width: `${prob}%`, backgroundColor: color }}
            />
          </div>
          <span className="text-[10px] sm:text-xs font-mono flex-shrink-0" style={{ color }}>
            {Math.round(prob)}% AI
          </span>
        </div>
      </div>
    </div>
  );
}
