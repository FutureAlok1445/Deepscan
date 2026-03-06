import { useState, useCallback } from 'react';
import { analyzeFile, analyzeUrl } from '../api/deepscan';

const ANALYSIS_STEPS = [
  'Extracting video keyframes...',
  'Running FFT spatial analysis...',
  'Analyzing optical flow (temporal)...',
  'Noise fingerprint analysis...',
  'Physics engine (LTCA) scan...',
  'Cross-domain consistency check...',
  'Computing AACS confidence score...',
  'Generating forensic NLM report...',
  'Finalizing report...',
];

export default function useAnalysis() {
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');

  const analyze = useCallback((file) => {
    setStatus('uploading');
    setError(null);
    setResult(null);
    setProgress(0);
    setCurrentStep('Uploading file...');

    let analysisInterval = null;

    // Called by axios during upload — shows real bytes transferred (0→50%)
    const onUploadProgress = (evt) => {
      if (evt.total) {
        const uploadPct = Math.round((evt.loaded / evt.total) * 50);
        setProgress(uploadPct);
        const mb = (evt.loaded / 1024 / 1024).toFixed(1);
        const total = (evt.total / 1024 / 1024).toFixed(1);
        setCurrentStep(`Uploading: ${mb} / ${total} MB`);

        if (evt.loaded >= evt.total) {
          // Upload complete — switch to analysis steps (50→95%)
          setStatus('analyzing');
          setCurrentStep(ANALYSIS_STEPS[0]);
          let step = 0;
          analysisInterval = setInterval(() => {
            if (step < ANALYSIS_STEPS.length) {
              setCurrentStep(ANALYSIS_STEPS[step]);
              setProgress(50 + Math.round(((step + 1) / ANALYSIS_STEPS.length) * 45));
              step++;
            } else {
              clearInterval(analysisInterval);
            }
          }, 800);
        }
      }
    };

    const promise = analyzeFile(file, onUploadProgress);

    promise
      .then((data) => {
        clearInterval(analysisInterval);
        setProgress(100);
        setCurrentStep('Analysis complete!');
        setResult(data);
        setStatus('complete');
      })
      .catch((err) => {
        clearInterval(analysisInterval);
        const msg = err?.response?.data?.detail
          || err?.message
          || 'Analysis failed. Please try again.';
        setError(msg);
        setStatus('error');
      });

    return promise;
  }, []);

  const analyzeByUrl = useCallback((url) => {
    setStatus('analyzing');
    setError(null);
    setResult(null);
    setProgress(10);
    setCurrentStep('Fetching media from URL...');

    let step = 0;
    const interval = setInterval(() => {
      if (step < ANALYSIS_STEPS.length) {
        setCurrentStep(ANALYSIS_STEPS[step]);
        setProgress(10 + Math.round(((step + 1) / ANALYSIS_STEPS.length) * 85));
        step++;
      } else {
        clearInterval(interval);
      }
    }, 600);

    const promise = analyzeUrl(url);
    promise
      .then((data) => { clearInterval(interval); setProgress(100); setCurrentStep('Analysis complete!'); setResult(data); setStatus('complete'); })
      .catch((err) => { clearInterval(interval); setError(err?.message || 'Analysis failed.'); setStatus('error'); });

    return promise;
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setResult(null);
    setError(null);
    setProgress(0);
    setCurrentStep('');
  }, []);

  return {
    status,
    result,
    error,
    progress,
    currentStep,
    steps: ANALYSIS_STEPS,
    analyze,
    analyzeByUrl,
    reset,
  };
}
