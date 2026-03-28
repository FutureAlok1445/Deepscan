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
import VideoResultDashboard from '../components/analysis/VideoResultDashboard';
import ImageResultDashboard from '../components/analysis/ImageResultDashboard';
import KeyFindings from '../components/analysis/KeyFindings';
import CdcfPanel from '../components/analysis/CdcfPanel';
import ForensicsViewer from '../components/analysis/ForensicsViewer';
import SubScoreGrid from '../components/analysis/SubScoreGrid';
import NarrativeExplanation from '../components/analysis/NarrativeExplanation';
import HeartbeatChart from '../components/analysis/HeartbeatChart';
import GradCamOverlay from '../components/analysis/GradCamOverlay';
import AudioSpectrum from '../components/analysis/AudioSpectrum';
import TrajectoryPlot from '../components/analysis/TrajectoryPlot';
import DetectionBreakdown from '../components/analysis/DetectionBreakdown';
import VideoDescription from '../components/analysis/VideoDescription';
import ElaHeatmapViewer from '../components/analysis/ElaHeatmapViewer';
import AnalysisReportGenerator from '../components/analysis/AnalysisReportGenerator';

function mapElaVerdictToLabel(verdict) {
  if (verdict === 'FAKE') return 'DEFINITELY FAKE';
  if (verdict === 'PARTIAL') return 'LIKELY AI';
  return 'AUTHENTIC';
}

export default function Result() {
  const { id } = useParams();
  const location = useLocation();
  const originalFile = location.state?.originalFile || null;

  const resultRef = useRef(null);
  const [simpleMode, setSimpleMode] = useState(false);
  const [localElaScore, setLocalElaScore] = useState(null);

  const { data: result, isLoading, error } = useQuery({
    queryKey: ['result', id],
    queryFn: () => getResult(id),
    retry: 1,
  });

  useEffect(() => {
    if (!resultRef.current || !result) return;
    const ctx = gsap.context(() => {
      gsap.from('.result-section', {
        y: 30,
        opacity: 0,
        duration: 0.5,
        stagger: 0.08,
        ease: 'power2.out',
      });
    }, resultRef);
    return () => ctx.revert();
  }, [result]);

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

  const verdictConfig = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.UNCERTAIN;
  const score = result.score ?? result.aacs_score ?? 0;
  const contextResult = result.context_result || result.context;

  const displayScore = localElaScore?.score ?? score;
  const displayVerdictLabel = localElaScore
    ? mapElaVerdictToLabel(localElaScore.verdict)
    : verdictConfig.label;

  return (
    <div ref={resultRef} className="relative min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between gap-4 result-section">
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 text-sm font-mono text-ds-silver/50 hover:text-ds-silver transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Analyze
          </Link>

          {(isVideo || isImage) && (
            <BrutalButton
              variant="secondary"
              size="sm"
              onClick={() => setSimpleMode((v) => !v)}
            >
              {simpleMode ? 'Full Report' : 'Simple View'}
            </BrutalButton>
          )}
        </div>

        {isImage && result.forensics?.ela && (
          <div className="result-section">
            <ElaHeatmapViewer
              elaData={result.forensics.ela}
              imageFile={originalFile}
              onScoreComputed={setLocalElaScore}
            />
          </div>
        )}

        <div className="result-section">
          <BrutalCard className="space-y-4">
            <div className="flex items-start justify-between flex-wrap gap-2">
              <div>
                <h1 className="font-grotesk font-black text-xl sm:text-2xl text-ds-silver">Analysis Result</h1>
                <p className="text-xs font-mono text-ds-silver/40 mt-1">
                  ID: {result.id || id} &bull; {formatDateTime(result.created_at)}
                </p>
                {localElaScore && (
                  <div className="mt-4 flex items-center gap-2 text-sm font-mono text-ds-silver mb-2 border border-ds-silver/20 p-2 rounded max-w-fit">
                    <span className="font-bold">System Score:</span>
                    <span
                      className="px-2 py-0.5 text-white rounded text-xs uppercase tracking-widest"
                      style={{
                        background:
                          localElaScore.score > 62
                            ? '#ff4422'
                            : localElaScore.score > 32
                              ? '#ffaa00'
                              : '#00cc55',
                      }}
                    >
                      ELA ANOMALY: {localElaScore.score}%
                    </span>
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <DownloadReport
                  resultId={result.id || id}
                  currentScore={displayScore}
                  currentVerdict={displayVerdictLabel}
                />
              </div>
            </div>

            {result.filename && (
              <div className="flex items-center gap-4 p-3 bg-ds-bg border border-ds-silver/20">
                <div className="text-xs font-mono text-ds-silver/50 space-y-1">
                  <p>File: <span className="text-ds-silver">{result.filename}</span></p>
                  {result.file_type && <p>Type: <span className="text-ds-silver">{result.file_type}</span></p>}
                  {result.processing_time_ms && (
                    <p>
                      Processing: <span className="text-ds-silver">{(result.processing_time_ms / 1000).toFixed(1)}s</span>
                    </p>
                  )}
                </div>
              </div>
            )}

            <div className="flex flex-wrap items-end gap-4">
              <span className={`text-4xl sm:text-5xl font-grotesk font-black ${getScoreColor(displayScore)}`}>
                {formatScore(displayScore)}
              </span>
              <div>
                <BrutalBadge
                  variant={displayScore >= 70 ? 'red' : displayScore >= 40 ? 'yellow' : 'green'}
                >
                  {displayVerdictLabel}
                </BrutalBadge>
                <p className="text-[10px] font-mono text-ds-silver/35 mt-2">
                  Higher score means higher deepfake probability.
                </p>
              </div>
            </div>

            <ShareVerdict verdict={displayVerdictLabel} score={displayScore} resultId={result.id || id} />
          </BrutalCard>
        </div>

        {simpleMode ? (
          <div className="result-section">
            <SimpleResult
              aacs_score={displayScore}
              verdict={displayVerdictLabel}
              plain_reason={result.narrative || result.explainability?.text || 'No detailed summary available.'}
              action={{
                label: 'Back to full report',
                onClick: () => setSimpleMode(false),
              }}
              context={contextResult}
            />
          </div>
        ) : (
          <>
            {result.ltca_data?.video_description && (
              <div className="result-section">
                <VideoDescription videoDescription={result.ltca_data.video_description} />
              </div>
            )}

            <div className="result-section">
              <AnalysisReportGenerator result={result} sysScore={displayScore} />
            </div>

            {isVideo && (
              <div className="result-section">
                <VideoResultDashboard result={result} />
              </div>
            )}

            {isImage && (
              <div className="result-section">
                <ImageResultDashboard result={result} originalFile={originalFile} />
              </div>
            )}

            {isAudio && (
              <>
                {result.findings?.length > 0 && (
                  <div className="result-section">
                    <KeyFindings findings={result.findings} />
                  </div>
                )}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
                  {result.audio && <AudioSpectrum audioData={result.audio} />}
                  {result.sub_scores && <SubScoreGrid subScores={result.sub_scores} />}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
                  <CdcfPanel cdcf={result.cdcf} />
                  <NarrativeExplanation narrative={result.narrative} />
                </div>
              </>
            )}

            {!isAudio && (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section items-start">
                  <div className="space-y-6 w-full flex flex-col">
                    {result.findings?.length > 0 && <KeyFindings findings={result.findings} />}
                    {result.sub_scores && <SubScoreGrid subScores={result.sub_scores} />}
                    <CdcfPanel cdcf={result.cdcf} />
                  </div>
                  <div className="space-y-6 w-full flex flex-col">
                    {(result.findings?.length > 0 || result.ltca_data) && (
                      <DetectionBreakdown
                        findings={result.findings || []}
                        ltcaData={result.ltca_data || {}}
                      />
                    )}
                    <NarrativeExplanation narrative={result.narrative} />
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 result-section">
                  {result.heartbeat && <HeartbeatChart heartbeatData={result.heartbeat} />}
                  {result.audio && <AudioSpectrum audioData={result.audio} />}
                  {result.ltca_data?.trajectory_plot?.length > 0 && (
                    <div className="lg:col-span-2">
                      <TrajectoryPlot trajectoryData={result.ltca_data.trajectory_plot} />
                    </div>
                  )}
                </div>
              </>
            )}

            {(result.forensics || result.gradcam) && (
              <div className="result-section mt-8">
                <details className="group [&_summary::-webkit-details-marker]:hidden border-2 border-ds-silver/20 hover:border-ds-red transition-all">
                  <summary className="flex items-center justify-between cursor-pointer p-4 bg-[#111] outline-none font-mono text-xs uppercase tracking-widest text-ds-silver/70 hover:text-ds-silver">
                    <span className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-ds-silver/40 group-open:bg-ds-red transition-colors" />
                      View Raw Backend Forensics
                    </span>
                    <span className="transition duration-300 group-open:rotate-180">▼</span>
                  </summary>
                  <div className="p-4 border-t-2 border-ds-silver/20 bg-[#0a0a0f] space-y-6">
                    {result.forensics && <ForensicsViewer forensics={result.forensics} />}
                    {result.gradcam && <GradCamOverlay gradcam={result.gradcam} />}
                  </div>
                </details>
              </div>
            )}
          </>
        )}

        {!isVideo && !isImage && !isAudio && (
          <div className="result-section grid grid-cols-1 lg:grid-cols-3 gap-6">
            <BrutalCard className="flex flex-col items-center justify-center lg:col-span-1">
              <TrustScoreGauge score={displayScore} size={200} />
              <div className="mt-3 text-center">
                <BrutalBadge variant={displayScore >= 70 ? 'red' : displayScore >= 40 ? 'yellow' : 'green'} pulse>
                  {verdictConfig.emoji} {verdictConfig.label}
                </BrutalBadge>
              </div>
            </BrutalCard>
            <BrutalCard className="lg:col-span-2 space-y-3">
              <h2 className="font-grotesk font-black text-xl text-ds-silver">General Analysis</h2>
              <p className="text-sm font-mono text-ds-silver/60">Unknown media type fallback rendered.</p>
            </BrutalCard>
          </div>
        )}

        <div className="text-center pt-8 result-section">
          <BrutalButton as={Link} to="/analyze" size="lg">
            Scan Another File
          </BrutalButton>
        </div>
      </div>
    </div>
  );
}