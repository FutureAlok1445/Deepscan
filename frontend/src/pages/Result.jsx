import React, { useRef, useEffect, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Loader, AlertCircle } from 'lucide-react';
import gsap from 'gsap';
import { getResult } from '../api/deepscan';
import { VERDICT_CONFIG } from '../utils/constants';
import { formatScore, formatDateTime, getScoreColor } from '../utils/formatters';

import BrutalCard from '../components/ui/BrutalCard';
import BrutalBadge from '../components/ui/BrutalBadge';
import BrutalButton from '../components/ui/BrutalButton';
import SimpleResult from '../components/SimpleResult';
import TrustScoreGauge from '../components/analysis/TrustScoreGauge';
import ShareVerdict from '../components/accessibility/ShareVerdict';
import DownloadReport from '../components/accessibility/DownloadReport';
import ArbitrationSystem from '../components/analysis/ArbitrationSystem';

// — Video: new unified dashboard
import VideoResultDashboard from '../components/analysis/VideoResultDashboard';

// — Non-video legacy panels (audio / image)
import KeyFindings from '../components/analysis/KeyFindings';
import CdcfPanel from '../components/analysis/CdcfPanel';
import ForensicsViewer from '../components/analysis/ForensicsViewer';
import SubScoreGrid from '../components/analysis/SubScoreGrid';
import NarrativeExplanation from '../components/analysis/NarrativeExplanation';
import HeartbeatChart from '../components/analysis/HeartbeatChart';
import GradCamOverlay from '../components/analysis/GradCamOverlay';
import AudioSpectrum from '../components/analysis/AudioSpectrum';
import TrajectoryPlot from '../components/analysis/TrajectoryPlot';
import GrokNLMAnalysis from '../components/analysis/GrokNLMAnalysis';

export default function Result() {
  const { id } = useParams();
  const location = useLocation();
  const originalFile = location.state?.originalFile || null;
  const resultRef = useRef(null);
  const [simpleMode, setSimpleMode] = useState(false);

  const { data: result, isLoading, error } = useQuery({
    queryKey: ['result', id],
    queryFn: () => getResult(id),
    retry: 1,
  });

  // GSAP entry animation
  useEffect(() => {
    if (!resultRef.current || !result) return;
    const ctx = gsap.context(() => {
      gsap.from('.result-section', {
        y: 30,
        opacity: 0,
        duration: 0.5,
        stagger: 0.1,
        ease: 'power2.out',
      });
    }, resultRef);
    return () => ctx.revert();
  }, [result]);

  // ─── Loading ───
  if (isLoading) {
    return (
      <div className="min-h-screen bg-ds-bg flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-10 h-10 text-ds-red animate-spin mx-auto mb-4" />
          <p className="font-mono text-sm text-ds-silver/50">Loading analysis result...</p>
        </div>
      </div>
    );
  }

  // ─── Error ───
  if (error || !result) {
    return (
      <div className="min-h-screen bg-ds-bg flex items-center justify-center px-4">
        <BrutalCard className="max-w-md text-center">
          <AlertCircle className="w-10 h-10 text-ds-red mx-auto mb-4" />
          <h2 className="font-grotesk font-bold text-xl text-ds-silver mb-2">Result Not Found</h2>
          <p className="text-sm font-mono text-ds-silver/50 mb-4">
            {error?.message || 'The analysis result could not be loaded.'}
          </p>
          <BrutalButton as={Link} to="/analyze" variant="secondary">
            Try Another Scan
          </BrutalButton>
        </BrutalCard>
      </div>
    );
  }

  const isVideo = result.file_type?.includes('video') || result.file_type === 'video';
  const isImage = result.file_type?.includes('image') || result.file_type === 'image';
  const isAudio = result.file_type?.includes('audio') || result.file_type === 'audio';

  const verdict = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.UNCERTAIN;
  const score = result.score ?? result.aacs_score ?? 0;
  const contextResult = result.context_result || result.context;

  return (
    <div ref={resultRef} className="relative min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* ── Top bar ── */}
        <div className="flex items-center justify-between gap-4 result-section">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 text-sm font-mono text-ds-silver/50 hover:text-ds-silver transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Analyze
          </Link>
          {isVideo && (
            <BrutalButton
              variant="secondary"
              size="sm"
              onClick={() => setSimpleMode(v => !v)}
            >
              {simpleMode ? 'Full Report' : 'Simple View'}
            </BrutalButton>
          )}
        </div>

        {/* ── Simple View ── */}
        {simpleMode ? (
          <div className="result-section">
            <SimpleResult
              aacs_score={score}
              verdict={verdict.label}
              plain_reason={result.narrative || result.explainability?.text}
              action={{
                label: 'Back to full report',
                onClick: () => setSimpleMode(false),
              }}
              context={contextResult}
            />
          </div>
        ) : (
          <>
            {/* ── Header Card (always visible) ── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 result-section">
              {/* Score gauge */}
              <BrutalCard className="flex flex-col items-center justify-center lg:col-span-1">
                <TrustScoreGauge score={score} size={typeof window !== 'undefined' && window.innerWidth < 640 ? 160 : 200} />
                <div className="mt-3 text-center">
                  <BrutalBadge
                    variant={score >= 70 ? 'red' : score >= 40 ? 'yellow' : 'green'}
                    pulse
                  >
                    {verdict.emoji} {verdict.label}
                  </BrutalBadge>
                </div>
              </BrutalCard>

              {/* Details */}
              <BrutalCard className="lg:col-span-2 space-y-3">
                <div className="flex items-start justify-between flex-wrap gap-2">
                  <div>
                    <h1 className="font-grotesk font-black text-xl sm:text-2xl text-ds-silver">
                      Analysis Result
                    </h1>
                    <p className="text-xs font-mono text-ds-silver/40 mt-1">
                      ID: {result.id || id} &bull; {formatDateTime(result.created_at)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <DownloadReport resultId={result.id || id} />
                  </div>
                </div>

                {result.filename && (
                  <div className="flex items-center gap-4 p-3 bg-ds-bg border border-ds-silver/20 rounded-sm">
                    <div className="text-xs font-mono text-ds-silver/50 space-y-0.5">
                      <p>File: <span className="text-ds-silver">{result.filename}</span></p>
                      {result.file_type && <p>Type: <span className="text-ds-silver capitalize">{result.file_type}</span></p>}
                      {result.processing_time_ms && (
                        <p>Processed in: <span className="text-ds-silver">{(result.processing_time_ms / 1000).toFixed(1)}s</span></p>
                      )}
                    </div>
                  </div>
                )}

                <ShareVerdict verdict={verdict.label} score={score} resultId={result.id || id} />

                <div className="flex items-baseline gap-3">
                  <span className={`text-4xl sm:text-5xl font-grotesk font-black ${getScoreColor(score)}`}>
                    {formatScore(score)}
                  </span>
                  <div>
                    <span className="text-xs sm:text-sm font-mono text-ds-silver/40">AACS Score</span>
                    <p className="text-[10px] font-mono text-ds-silver/25 mt-0.5">Higher = more likely AI-generated</p>
                  </div>
                </div>
              </BrutalCard>
            </div>

            {/* ══════════ VIDEO — New Tabbed Dashboard ══════════ */}
            {isVideo && (
              <div className="result-section">
                <VideoResultDashboard result={result} />
              </div>
            )}

            {/* ══════════ IMAGE ══════════ */}
            {isImage && (
              <>
                <div className="result-section">
                  <ArbitrationSystem imageFile={originalFile} backendScore={score} />
                </div>
                <div className="result-section">
                  <KeyFindings findings={result.findings || []} />
                </div>
                <div className="result-section">
                  <SubScoreGrid subScores={result.sub_scores} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
                  <CdcfPanel cdcf={result.cdcf} />
                  <NarrativeExplanation narrative={result.narrative} />
                </div>
                {result.forensics && (
                  <div className="result-section">
                    <ForensicsViewer forensics={result.forensics} />
                  </div>
                )}
                {result.gradcam && (
                  <div className="result-section">
                    <GradCamOverlay gradcam={result.gradcam} />
                  </div>
                )}
              </>
            )}

            {/* ══════════ AUDIO ══════════ */}
            {isAudio && (
              <>
                <div className="result-section">
                  <KeyFindings findings={result.findings || []} />
                </div>
                {result.audio && (
                  <div className="result-section">
                    <AudioSpectrum audioData={result.audio} />
                  </div>
                )}
                <div className="result-section">
                  <SubScoreGrid subScores={result.sub_scores} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
                  <CdcfPanel cdcf={result.cdcf} />
                  <NarrativeExplanation narrative={result.narrative} />
                </div>
              </>
            )}

            {/* ══════════ FALLBACK (unknown type) ══════════ */}
            {!isVideo && !isImage && !isAudio && (
              <>
                <div className="result-section">
                  <KeyFindings findings={result.findings || []} />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
                  <CdcfPanel cdcf={result.cdcf} />
                  <NarrativeExplanation narrative={result.narrative} />
                </div>
              </>
            )}

            {/* ── Bottom CTA ── */}
            <div className="text-center pt-8 result-section">
              <BrutalButton as={Link} to="/analyze" size="lg">
                Scan Another File
              </BrutalButton>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
