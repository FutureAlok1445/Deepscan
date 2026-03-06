import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  Upload, Link2, Camera, FileVideo, FileImage, FileAudio, X, AlertCircle, Shield, Zap, Fingerprint,
} from 'lucide-react';
import gsap from 'gsap';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalButton from '../components/ui/BrutalButton';
import LiveProgressPanel from '../components/analysis/LiveProgressPanel';
import useAnalysis from '../hooks/useAnalysis';
import { ACCEPTED_FILE_TYPES } from '../utils/constants';
import { truncateFilename, formatFileSize } from '../utils/formatters';

const TABS = [
  { id: 'upload', label: 'Upload', icon: Upload },
  { id: 'url', label: 'URL', icon: Link2 },
  { id: 'camera', label: 'Camera', icon: Camera },
];

export default function Analyze() {
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const navigate = useNavigate();
  const { status, progress, currentStep, error, analyze, analyzeByUrl, reset } = useAnalysis();
  const pageRef = useRef(null);

  // GSAP entry animation
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.analyze-header', { y: -40, opacity: 0, duration: 0.7, ease: 'power3.out' });
      gsap.from('.analyze-tabs', { y: 20, opacity: 0, duration: 0.5, delay: 0.2, ease: 'power2.out' });
      gsap.from('.analyze-content', { y: 30, opacity: 0, duration: 0.6, delay: 0.35, ease: 'power2.out' });
      gsap.from('.analyze-cta', { scale: 0.9, opacity: 0, duration: 0.5, delay: 0.5, ease: 'back.out(1.7)' });
    }, pageRef);
    return () => ctx.revert();
  }, []);

  const onDrop = useCallback((accepted) => {
    if (accepted.length > 0) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: false,
  });

  const handleAnalyze = async () => {
    try {
      let result;
      if (activeTab === 'url' && url) {
        result = await analyzeByUrl(url);
      } else if (file) {
        result = await analyze(file);
      }
      if (result?.id) {
        navigate(`/result/${result.id}`, { state: { originalFile: file } });
      } else if (result) {
        navigate('/result/demo', { state: { originalFile: file } });
      }
    } catch {
      // error is handled in hook
    }
  };

  const isAnalyzing = status === 'uploading' || status === 'analyzing';

  if (isAnalyzing) {
    return (
      <div className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <LiveProgressPanel progress={progress} currentStep={currentStep} />
        </div>
      </div>
    );
  }

  return (
    <div ref={pageRef} className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      {/* Floating particles background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 rounded-full bg-ds-red/20 animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${2 + Math.random() * 3}s`,
            }}
          />
        ))}
      </div>

      <div className="max-w-2xl mx-auto space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center analyze-header">
          <div className="inline-flex items-center gap-2 mb-4">
            <Fingerprint className="w-5 h-5 text-ds-cyan animate-pulse" />
            <p className="text-xs font-mono text-ds-red uppercase tracking-[0.3em]">
              // ANALYZE
            </p>
            <Zap className="w-5 h-5 text-ds-yellow animate-pulse" />
          </div>
          <h1 className="text-3xl md:text-5xl font-grotesk font-black text-ds-silver">
            Scan for <span className="text-ds-red drop-shadow-[0_0_20px_rgba(255,60,0,0.5)]">Deepfakes</span>
          </h1>
          <p className="mt-3 text-sm font-mono text-ds-silver/50">
            Upload an image, video, or audio file for AI-powered analysis
          </p>
        </div>

        {/* Tab bar */}
        <div className="flex border-b-3 border-ds-silver/20 analyze-tabs">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); reset(); }}
              className={`flex items-center gap-1.5 sm:gap-2 px-3 sm:px-6 py-2.5 sm:py-3 font-mono text-xs sm:text-sm uppercase tracking-wider transition-all duration-300 ${activeTab === id
                  ? 'text-ds-red border-b-3 border-ds-red bg-ds-red/5 shadow-[0_4px_20px_rgba(255,60,0,0.15)]'
                  : 'text-ds-silver/50 hover:text-ds-silver hover:bg-ds-silver/5'
                }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="space-y-4 analyze-content">
            <div
              {...getRootProps()}
              className={`border-3 border-dashed p-6 sm:p-12 text-center cursor-pointer transition-all duration-300 group relative overflow-hidden ${isDragActive
                  ? 'border-ds-red bg-ds-red/10 shadow-[0_0_40px_rgba(255,60,0,0.2)]'
                  : 'border-ds-silver/30 hover:border-ds-cyan/60 hover:shadow-[0_0_30px_rgba(0,245,255,0.1)]'
                }`}
            >
              <input {...getInputProps()} />
              {/* Animated corner decorations */}
              <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-ds-cyan/40 transition-all group-hover:w-12 group-hover:h-12 group-hover:border-ds-cyan" />
              <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-ds-cyan/40 transition-all group-hover:w-12 group-hover:h-12 group-hover:border-ds-cyan" />
              <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-ds-cyan/40 transition-all group-hover:w-12 group-hover:h-12 group-hover:border-ds-cyan" />
              <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-ds-cyan/40 transition-all group-hover:w-12 group-hover:h-12 group-hover:border-ds-cyan" />

              <Upload className="w-12 h-12 mx-auto text-ds-silver/30 mb-4 group-hover:text-ds-cyan transition-colors group-hover:scale-110 transform duration-300" />
              <p className="font-grotesk font-bold text-lg text-ds-silver">
                {isDragActive ? 'Drop it here!' : 'Drag & drop media file'}
              </p>
              <p className="text-xs font-mono text-ds-silver/40 mt-2">
                JPG, PNG, MP4, AVI, WAV, MP3 — up to 100MB
              </p>
            </div>

            {file && (
              <BrutalCard hover={false} className="flex items-center gap-4">
                <FileIcon type={file.type} />
                <div className="flex-1 min-w-0">
                  <p className="font-mono text-sm text-ds-silver truncate">
                    {truncateFilename(file.name, 40)}
                  </p>
                  <p className="text-xs font-mono text-ds-silver/40">
                    {formatFileSize(file.size)} • {file.type}
                  </p>
                </div>
                <button onClick={() => setFile(null)} className="text-ds-silver/40 hover:text-ds-red">
                  <X className="w-5 h-5" />
                </button>
              </BrutalCard>
            )}
          </div>
        )}

        {/* URL Tab */}
        {activeTab === 'url' && (
          <div className="space-y-4">
            <BrutalCard hover={false}>
              <label className="block text-xs font-mono text-ds-silver/50 uppercase tracking-wider mb-2">
                Media URL
              </label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/video.mp4"
                  className="flex-1 bg-ds-bg border-3 border-ds-silver/30 px-4 py-3 font-mono text-sm text-ds-silver placeholder:text-ds-silver/20 focus:border-ds-red focus:outline-none transition-colors"
                />
              </div>
              <p className="text-xs font-mono text-ds-silver/30 mt-2">
                Paste a direct link to an image, video, or news article
              </p>
            </BrutalCard>
          </div>
        )}

        {/* Camera Tab */}
        {activeTab === 'camera' && (
          <BrutalCard hover={false} className="text-center py-12">
            <Camera className="w-12 h-12 mx-auto text-ds-silver/30 mb-4" />
            <p className="font-grotesk font-bold text-lg text-ds-silver mb-2">
              Camera Capture
            </p>
            <p className="text-sm font-mono text-ds-silver/40">
              Coming soon — capture a photo or short video directly from your device camera
            </p>
          </BrutalCard>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 p-4 bg-ds-red/10 border-3 border-ds-red">
            <AlertCircle className="w-5 h-5 text-ds-red flex-shrink-0" />
            <p className="text-sm font-mono text-ds-red">{error}</p>
          </div>
        )}

        {/* Analyze button */}
        <div className="text-center analyze-cta">
          <BrutalButton
            size="lg"
            onClick={handleAnalyze}
            disabled={activeTab === 'upload' ? !file : activeTab === 'url' ? !url : true}
            className="group relative overflow-hidden"
          >
            <Shield className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span>Analyze Now</span>
            <Zap className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
          </BrutalButton>
          <p className="mt-3 text-xs font-mono text-ds-silver/30">
            Powered by AACS — 5 parallel AI engines
          </p>
        </div>
      </div>
    </div>
  );
}

function FileIcon({ type }) {
  if (type?.startsWith('video')) return <FileVideo className="w-8 h-8 text-ds-cyan flex-shrink-0" />;
  if (type?.startsWith('audio')) return <FileAudio className="w-8 h-8 text-ds-yellow flex-shrink-0" />;
  return <FileImage className="w-8 h-8 text-ds-green flex-shrink-0" />;
}
