import { useState, useCallback } from 'react';
import { analyzeFile, analyzeUrl } from '../api/deepscan';

const STEPS = [
  'Validating file integrity...',
  'Running ELA forensic analysis...',
  'Analyzing audio spectrogram...',
  'Running EfficientNet-B4 classification...',
  'Extracting rPPG heartbeat signal...',
  'Cross-domain consistency check (CDCF)...',
  'Computing AACS confidence score...',
  'Generating Hindi narration...',
  'Preparing forensic report...',
];

export default function useAnalysis() {
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');

  const simulateSteps = useCallback((apiPromise) => {
    return new Promise((resolve) => {
      setStatus('analyzing');
      setProgress(0);
      let step = 0;
      const interval = setInterval(() => {
        if (step < STEPS.length) {
          setCurrentStep(STEPS[step]);
          setProgress(Math.min(Math.round(((step + 1) / STEPS.length) * 95), 95));
          step++;
        } else {
          clearInterval(interval);
        }
      }, 350);

      apiPromise
        .then((data) => {
          clearInterval(interval);
          setProgress(100);
          setCurrentStep('Analysis complete.');
          setResult(data);
          setStatus('complete');
          resolve(data);
        })
        .catch((err) => {
          clearInterval(interval);
          setError(err.message || 'Analysis failed');
          setStatus('error');
          resolve(null);
        });
    });
  }, []);

  const analyze = useCallback(
    (file, language = 'hi') => {
      setStatus('uploading');
      setError(null);
      setResult(null);
      const promise = analyzeFile(file, language);
      return simulateSteps(promise);
    },
    [simulateSteps]
  );

  const analyzeByUrl = useCallback(
    (url, language = 'hi') => {
      setStatus('uploading');
      setError(null);
      setResult(null);
      const promise = analyzeUrl(url, language);
      return simulateSteps(promise);
    },
    [simulateSteps]
  );

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
    steps: STEPS,
    analyze,
    analyzeByUrl,
    reset,
  };
}
