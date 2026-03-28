import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Zap, RefreshCw, AlertTriangle, CheckCircle, BarChart3, Binary, MessageSquare, BrainCircuit, Mail, Link as LinkIcon, Globe, Lock } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { analyzeText } from '../api/deepscan';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalButton from '../components/ui/BrutalButton';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MODES = [
  { id: 'ai', label: 'AI Detection', icon: BrainCircuit, color: 'text-ds-cyan' },
  { id: 'phishing', label: 'Phishing Scan', icon: Mail, color: 'text-ds-yellow' }
];

export default function TextAnalyze() {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('ai');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const resultRef = useRef(null);

  const handleAnalyze = async () => {
    if (!text || text.trim().length < 20) {
      toast.error('Please enter at least 20 characters of text.');
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      // Use centralized API service for consistency
      const data = await analyzeText(text, mode);
      setResult(data);
      toast.success('Analysis complete!');
      
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    } catch (error) {
      console.error('Analysis failed:', error);
      const detail = error.response?.data?.detail || error.message || 'Analysis failed. Please try again.';
      toast.error(detail);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score, isPhishing) => {
    if (isPhishing) {
      if (score < 20) return '#39ff14'; // Green (Safe)
      if (score < 50) return '#ffd700'; // Yellow (Warning)
      return '#ff3c00'; // Red (Danger)
    }
    if (score < 30) return '#39ff14'; // Green (Human)
    if (score < 60) return '#ffd700'; // Yellow (Uncertain)
    return '#ff3c00'; // Red (AI)
  };

  return (
    <div className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Header Section */}
        <div className="text-center space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-3 py-1 bg-ds-red/10 border border-ds-red/50 rounded-full"
          >
            <Binary className="w-4 h-4 text-ds-red" />
            <span className="text-[10px] font-mono text-ds-red uppercase tracking-widest font-black">
              NEURAL TEXT ANALYZER V2.0
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-4xl md:text-6xl font-grotesk font-black text-ds-silver"
          >
            {mode === 'ai' ? (
              <>Detect <span className="text-ds-red italic">AI-Generated</span> Content</>
            ) : (
              <>Scan for <span className="text-ds-yellow italic">Phishing</span> Risks</>
            )}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-ds-silver/50 font-mono text-sm max-w-2xl mx-auto"
          >
            {mode === 'ai'
              ? 'Our multi-engine detector analyzes Perplexity, Burstiness, and Model Consensus to identify GPT, Claude, and Gemini generated text.'
              : 'Our phishing engine scans for suspicious URLs, urgent language, and fake sender domains to protect you from malicious emails.'}
          </motion.p>
        </div>

        {/* Mode Selector */}
        <div className="flex justify-center gap-4">
          {MODES.map((m) => {
            const Icon = m.icon;
            const isActive = mode === m.id;
            return (
              <button
                key={m.id}
                onClick={() => { setMode(m.id); setResult(null); }}
                className={`flex items-center gap-3 px-6 py-3 border-3 transition-all duration-300 ${isActive
                    ? `border-ds-red bg-ds-red/10 text-ds-silver shadow-[0_0_20px_rgba(255,60,0,0.2)]`
                    : 'border-ds-silver/10 text-ds-silver/40 hover:border-ds-silver/30'
                  }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? m.color : ''}`} />
                <span className="font-mono text-sm font-bold uppercase tracking-wider">{m.label}</span>
              </button>
            );
          })}
        </div>

        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <BrutalCard className="relative p-0 overflow-hidden" hover={false}>
            <div className="bg-ds-silver/5 border-b-2 border-ds-silver/20 px-6 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full animate-ping ${mode === 'ai' ? 'bg-ds-cyan' : 'bg-ds-yellow'}`} />
                <span className="text-xs font-mono text-ds-silver uppercase tracking-wider">
                  Paste {mode === 'ai' ? 'text content' : 'email body'} below
                </span>
              </div>
              <span className="text-[10px] font-mono text-ds-silver/30">
                {text.length} characters
              </span>
            </div>

            <textarea
              className="w-full h-80 bg-transparent text-ds-silver font-mono text-sm p-6 focus:outline-none resize-none placeholder:text-ds-silver/10"
              placeholder={mode === 'ai' ? "Paste the text you want to analyze... (Minimum 20 chars)" : "Paste the email content including headers if available... (Minimum 20 chars)"}
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isLoading}
            />

            <div className="p-6 bg-ds-silver/5 border-t-2 border-ds-silver/20 flex flex-col md:flex-row gap-4 items-center justify-between">
              <div className="flex gap-4">
                {mode === 'ai' ? (
                  <>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-ds-cyan">
                      <BrainCircuit className="w-3 h-3" /> GPT-2 Check
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-ds-yellow">
                      <BarChart3 className="w-3 h-3" /> Burstiness
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-ds-yellow">
                      <LinkIcon className="w-3 h-3" /> Link Scan
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-ds-red">
                      <Globe className="w-3 h-3" /> Domain Check
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono text-ds-cyan">
                      <Zap className="w-3 h-3" /> Urgency
                    </div>
                  </>
                )}
              </div>

              <BrutalButton
                onClick={handleAnalyze}
                disabled={isLoading || !text.trim()}
                className="w-full md:w-auto"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Shield className="w-4 h-4" />
                    <span>Run Analysis</span>
                    <Zap className="w-4 h-4 text-ds-yellow" />
                  </>
                )}
              </BrutalButton>
            </div>
          </BrutalCard>
        </motion.div>

        {/* Results Section */}
        <AnimatePresence>
          {result && (
            <motion.div
              ref={resultRef}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="space-y-8"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Score Card */}
                <BrutalCard className="flex flex-col items-center justify-center p-12 text-center" hover={false}>
                  <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle
                        cx="96"
                        cy="96"
                        r="88"
                        fill="transparent"
                        stroke="rgba(255,255,255,0.05)"
                        strokeWidth="12"
                      />
                      <motion.circle
                        cx="96"
                        cy="96"
                        r="88"
                        fill="transparent"
                        stroke={getScoreColor(result.overall_score, result.type === 'phishing')}
                        strokeWidth="12"
                        strokeDasharray={552.92}
                        initial={{ strokeDashoffset: 552.92 }}
                        animate={{ strokeDashoffset: 552.92 - (552.92 * result.overall_score) / 100 }}
                        transition={{ duration: 1.5, ease: "easeOut" }}
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <span className="text-5xl font-black font-grotesk text-ds-silver">
                        {Math.round(result.overall_score)}%
                      </span>
                      <span className="text-[10px] font-mono text-ds-silver/40 uppercase tracking-widest">
                        {result.type === 'ai' ? 'AI Probability' : 'Phishing Risk'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-8 space-y-2">
                    <h3 className="text-2xl font-black font-grotesk uppercase tracking-tighter" style={{ color: getScoreColor(result.overall_score, result.type === 'phishing') }}>
                      {result.verdict}
                    </h3>
                    <p className="text-xs font-mono text-ds-silver/50">
                      Analysis completed in {result.execution_time}s
                    </p>
                  </div>
                </BrutalCard>

                {/* Signals Card */}
                <BrutalCard className="p-8" hover={false}>
                  <h3 className="text-lg font-black font-grotesk text-ds-silver uppercase mb-6 flex items-center gap-2">
                    <Binary className="w-5 h-5 text-ds-red" />
                    Detection Signals
                  </h3>

                  <div className="space-y-6">
                    {result.type === 'ai' ? (
                      <>
                        <SignalRow label="Model Confidence" value={result.details?.signals?.hf_model ?? 0} sub="Neural pattern matching" color={getScoreColor(result.details?.signals?.hf_model ?? 0)} />
                        <SignalRow label="Perplexity" value={100 - ((result.details?.signals?.perplexity ?? 0) / 2)} sub="Text predictability" color={getScoreColor(100 - ((result.details?.signals?.perplexity ?? 0) / 2))} />
                        <SignalRow label="Burstiness" value={100 - (result.details?.signals?.burstiness ?? 0)} sub="Sentence variance" color={getScoreColor(100 - (result.details?.signals?.burstiness ?? 0))} />
                        <SignalRow label="AI Debate" value={result.details?.signals?.sapling_api ?? 0} sub="Sapling / LLM Consensus" color={getScoreColor(result.details?.signals?.sapling_api ?? 0)} />
                      </>
                    ) : (
                      <>
                        <SignalRow label="Keywords" value={result.details?.signals?.keywords ?? 0} sub="Suspicious language" color="#ffd700" />
                        <SignalRow label="Links" value={result.details?.signals?.links ?? 0} sub="URL reputation" color="#ff3c00" />
                        <SignalRow label="Headers" value={result.details?.signals?.headers ?? 0} sub="Source verification" color="#ff3c00" />
                      </>
                    )}
                  </div>
                </BrutalCard>
              </div>

              {/* Reasons & Insight */}
              <BrutalCard className={`p-8 ${result.overall_score > 60 ? 'border-ds-red/30' : 'border-ds-cyan/30'}`} hover={false}>
                <div className="flex items-start gap-6">
                  <div className={`hidden md:flex w-16 h-16 bg-ds-cyan/10 border-2 border-ds-cyan/30 items-center justify-center flex-shrink-0 ${result.overall_score > 60 ? 'bg-ds-red/10 border-ds-red/30' : ''}`}>
                    {result.type === 'ai' ? <BrainCircuit className="w-8 h-8 text-ds-cyan" /> : <Shield className="w-8 h-8 text-ds-red" />}
                  </div>
                  <div className="space-y-4 flex-1">
                    <h3 className="text-xl font-black font-grotesk text-ds-silver uppercase">
                      Forensic Insights
                    </h3>
                    <ul className="space-y-3">
                      {(result.details?.reasons || ['Analysis complete.']).map((reason, idx) => (
                        <motion.li
                          key={idx}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.5 + (idx * 0.1) }}
                          className="flex items-center gap-3 text-sm font-mono text-ds-silver/70"
                        >
                          <div className={`w-1.5 h-1.5 ${result.overall_score > 60 ? 'bg-ds-red' : 'bg-ds-green'}`} />
                          {reason}
                        </motion.li>
                      ))}
                    </ul>
                  </div>
                </div>
              </BrutalCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Info Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureInfo
            icon={mode === 'ai' ? Zap : LinkIcon}
            title={mode === 'ai' ? "Statistical" : "Link Analysis"}
            desc={mode === 'ai' ? "Analyzes token predictability and n-gram overlap." : "Cross-references URLs against phishing databases and suspicious TLDs."}
          />
          <FeatureInfo
            icon={mode === 'ai' ? BarChart3 : Globe}
            title={mode === 'ai' ? "Structural" : "Domain Check"}
            desc={mode === 'ai' ? "Detects unnatural sentence length variance." : "Identifies spoofed sender domains and irregular header patterns."}
          />
          <FeatureInfo
            icon={mode === 'ai' ? CheckCircle : Lock}
            title={mode === 'ai' ? "Consensus" : "Risk Scoring"}
            desc={mode === 'ai' ? "Cross-references patterns with known LLM datasets." : "Uses weighted heuristic analysis to calculate total phishing probability."}
          />
        </div>
      </div>
    </div>
  );
}

function SignalRow({ label, value, sub, color }) {
  const normValue = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-end">
        <div>
          <p className="text-sm font-bold font-grotesk text-ds-silver uppercase">{label}</p>
          <p className="text-[10px] font-mono text-ds-silver/30">{sub}</p>
        </div>
        <span className="text-xs font-mono font-bold" style={{ color: color || '#ff3c00' }}>
          {Math.round(normValue)}%
        </span>
      </div>
      <div className="h-1.5 bg-ds-silver/5 border border-ds-silver/10">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${normValue}%` }}
          transition={{ duration: 1, delay: 0.5 }}
          className="h-full"
          style={{ backgroundColor: color || '#ff3c00' }}
        />
      </div>
    </div>
  );
}

function FeatureInfo({ icon: Icon, title, desc }) {
  return (
    <div className="p-6 border-b-3 md:border-b-0 md:border-r-3 border-ds-silver/10 last:border-0">
      <Icon className="w-6 h-6 text-ds-red mb-4" />
      <h4 className="text-sm font-black font-grotesk text-ds-silver uppercase mb-2">{title}</h4>
      <p className="text-xs font-mono text-ds-silver/40 leading-relaxed">{desc}</p>
    </div>
  );
}
