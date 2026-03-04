import React, { useState, useLayoutEffect, useRef } from 'react';
import {
  BookOpen, HelpCircle, CheckCircle, XCircle, ChevronDown, ChevronUp,
  Brain, Eye, Shield, Fingerprint,
} from 'lucide-react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import BrutalCard from '../components/ui/BrutalCard';
import BrutalButton from '../components/ui/BrutalButton';
import BrutalBadge from '../components/ui/BrutalBadge';

gsap.registerPlugin(ScrollTrigger);

/* ─── Quiz Data ─── */
const QUIZ = [
  {
    q: 'Which of these is a common sign of a deepfake video?',
    options: [
      'Natural eye blinking patterns',
      'Unnatural lip movements that don\'t match audio',
      'Consistent lighting across frames',
      'Smooth skin texture throughout',
    ],
    answer: 1,
    explanation: 'Lip-sync artifacts are among the most reliable indicators. Deepfake generators still struggle with perfectly matching mouth movements to speech audio.',
  },
  {
    q: 'What does ELA stand for in forensic analysis?',
    options: [
      'Electronic Light Analysis',
      'Error Level Analysis',
      'Enhanced Layer Assessment',
      'Edge Line Accuracy',
    ],
    answer: 1,
    explanation: 'Error Level Analysis detects different compression levels in an image, revealing areas that have been modified or spliced.',
  },
  {
    q: 'What is rPPG used for in deepfake detection?',
    options: [
      'Detecting font manipulation',
      'Measuring remote photoplethysmography (heartbeat)',
      'Reverse image searching',
      'Audio frequency analysis',
    ],
    answer: 1,
    explanation: 'rPPG extracts subtle color changes in facial skin caused by blood flow. Real faces show natural heartbeat signals; deepfakes typically don\'t.',
  },
  {
    q: 'What percentage of Indians can detect deepfakes according to recent studies?',
    options: ['75%', '50%', '25%', '4%'],
    answer: 3,
    explanation: 'Studies show only about 4% of Indians can reliably identify deepfake content, making automated detection tools essential.',
  },
];

/* ─── Glossary ─── */
const GLOSSARY = [
  { term: 'Deepfake', def: 'AI-generated or AI-manipulated media (images, video, audio) designed to deceive.' },
  { term: 'GAN', def: 'Generative Adversarial Network — two neural networks competing to create realistic fake content.' },
  { term: 'Face Swap', def: 'Technique of replacing one person\'s face with another in a video or image.' },
  { term: 'ELA', def: 'Error Level Analysis — forensic technique revealing JPEG compression inconsistencies.' },
  { term: 'FFT', def: 'Fast Fourier Transform — frequency-domain analysis to detect periodic artifacts from GAN generation.' },
  { term: 'rPPG', def: 'Remote Photoplethysmography — extracting heart rate signals from video of skin color changes.' },
  { term: 'CDCF', def: 'Consensus-Driven Cross-Fusion — DeepScan\'s proprietary fusion method combining multiple detector outputs.' },
  { term: 'Grad-CAM', def: 'Gradient-weighted Class Activation Mapping — visual explanation of what regions influenced the AI\'s decision.' },
  { term: 'Lip Sync', def: 'The synchronization between mouth movements and spoken audio in a video.' },
  { term: 'Metadata', def: 'Embedded information in files (EXIF, creation date, software) that can reveal manipulation history.' },
];

/* ─── Info Cards ─── */
const INFO_CARDS = [
  {
    icon: Brain,
    title: 'How AI Creates Deepfakes',
    body: 'GANs and diffusion models learn from millions of real images to generate synthetic media. Modern tools like DALL-E and Midjourney make creation accessible to anyone.',
  },
  {
    icon: Eye,
    title: 'How DeepScan Detects Them',
    body: '8 specialized neural networks analyze face-swaps, lip-sync, forensic artifacts, physiological signals, audio anomalies, metadata, and contextual clues simultaneously.',
  },
  {
    icon: Shield,
    title: 'Protecting Yourself',
    body: 'Always verify suspicious media using tools like DeepScan. Check for unnatural blinking, lip movements, lighting inconsistencies, and reverse-image search.',
  },
  {
    icon: Fingerprint,
    title: 'The Indian Context',
    body: 'India faces unique challenges with political deepfakes, financial fraud via voice cloning, and misinformation in 8+ regional languages.',
  },
];

export default function Learn() {
  const pageRef = useRef(null);

  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.learn-header', { y: -30, opacity: 0, duration: 0.6, ease: 'power3.out' });
      gsap.from('.learn-card', { y: 40, opacity: 0, stagger: 0.12, duration: 0.6, delay: 0.2, ease: 'power2.out' });
      gsap.from('.learn-quiz', {
        scrollTrigger: { trigger: '.learn-quiz', start: 'top 85%' },
        y: 40, opacity: 0, duration: 0.6, ease: 'power2.out',
      });
      gsap.from('.learn-glossary', {
        scrollTrigger: { trigger: '.learn-glossary', start: 'top 85%' },
        y: 40, opacity: 0, duration: 0.6, ease: 'power2.out',
      });
    }, pageRef);
    return () => ctx.revert();
  }, []);

  return (
    <div ref={pageRef} className="min-h-screen bg-ds-bg pt-24 pb-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Decorative grid lines */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{ backgroundImage: 'linear-gradient(to right, #e0e0e0 1px, transparent 1px), linear-gradient(to bottom, #e0e0e0 1px, transparent 1px)', backgroundSize: '60px 60px' }}
      />

      <div className="max-w-4xl mx-auto space-y-12 relative z-10">
        {/* Header */}
        <div className="text-center learn-header">
          <p className="text-xs font-mono text-ds-yellow uppercase tracking-[0.3em] mb-2">
            // EDUCATION
          </p>
          <h1 className="text-3xl md:text-4xl font-grotesk font-black text-ds-silver">
            Learn About <span className="text-ds-yellow">Deepfakes</span>
          </h1>
          <p className="mt-2 text-sm font-mono text-ds-silver/50">
            Understand the technology, the threats, and how to protect yourself
          </p>
        </div>

        {/* Infographic cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {INFO_CARDS.map((card, i) => (
            <BrutalCard key={i} className="learn-card">
              <card.icon className="w-8 h-8 text-ds-yellow mb-3" />
              <h3 className="font-grotesk font-bold text-lg text-ds-silver mb-2">{card.title}</h3>
              <p className="text-sm font-mono text-ds-silver/60 leading-relaxed">{card.body}</p>
            </BrutalCard>
          ))}
        </div>

        {/* Quiz */}
        <div className="learn-quiz">
          <QuizSection />
        </div>

        {/* Glossary */}
        <section className="space-y-4 learn-glossary">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-ds-cyan" />
            <h2 className="font-grotesk font-bold text-xl text-ds-silver uppercase tracking-wider">
              Glossary
            </h2>
          </div>
          <div className="space-y-2">
            {GLOSSARY.map((item, i) => (
              <GlossaryItem key={i} {...item} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function QuizSection() {
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState(null);
  const [answered, setAnswered] = useState(false);
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);

  const q = QUIZ[current];

  const handleSelect = (idx) => {
    if (answered) return;
    setSelected(idx);
    setAnswered(true);
    if (idx === q.answer) setScore((s) => s + 1);
  };

  const handleNext = () => {
    if (current + 1 >= QUIZ.length) {
      setFinished(true);
    } else {
      setCurrent((c) => c + 1);
      setSelected(null);
      setAnswered(false);
    }
  };

  const handleRestart = () => {
    setCurrent(0);
    setSelected(null);
    setAnswered(false);
    setScore(0);
    setFinished(false);
  };

  if (finished) {
    return (
      <BrutalCard className="text-center py-10 space-y-4">
        <HelpCircle className="w-10 h-10 text-ds-yellow mx-auto" />
        <h3 className="font-grotesk font-bold text-2xl text-ds-silver">
          Quiz Complete!
        </h3>
        <p className="text-4xl font-grotesk font-black text-ds-yellow">
          {score}/{QUIZ.length}
        </p>
        <p className="text-sm font-mono text-ds-silver/50">
          {score === QUIZ.length ? 'Perfect score! You\'re a deepfake expert.' :
           score >= QUIZ.length / 2 ? 'Good job! Keep learning.' :
           'There\'s more to learn. Try again!'}
        </p>
        <BrutalButton onClick={handleRestart} variant="secondary">
          Try Again
        </BrutalButton>
      </BrutalCard>
    );
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-ds-yellow" />
          <h2 className="font-grotesk font-bold text-xl text-ds-silver uppercase tracking-wider">
            Quiz
          </h2>
        </div>
        <BrutalBadge variant="yellow">
          {current + 1}/{QUIZ.length}
        </BrutalBadge>
      </div>

      <BrutalCard className="space-y-4">
        <p className="font-grotesk font-bold text-lg text-ds-silver">{q.q}</p>

        <div className="space-y-2">
          {q.options.map((opt, i) => {
            let style = 'border-ds-silver/20 hover:border-ds-silver/60 text-ds-silver/70';
            if (answered) {
              if (i === q.answer) style = 'border-ds-green bg-ds-green/10 text-ds-green';
              else if (i === selected) style = 'border-ds-red bg-ds-red/10 text-ds-red';
              else style = 'border-ds-silver/10 text-ds-silver/30';
            }
            return (
              <button
                key={i}
                onClick={() => handleSelect(i)}
                className={`w-full text-left px-4 py-3 border-2 font-mono text-sm transition-colors flex items-center gap-3 ${style}`}
                disabled={answered}
              >
                <span className="w-6 h-6 flex items-center justify-center border border-current text-xs">
                  {answered && i === q.answer ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : answered && i === selected ? (
                    <XCircle className="w-4 h-4" />
                  ) : (
                    String.fromCharCode(65 + i)
                  )}
                </span>
                {opt}
              </button>
            );
          })}
        </div>

        {answered && (
          <div className="p-3 bg-ds-bg border-l-4 border-ds-yellow">
            <p className="text-sm font-mono text-ds-silver/70 leading-relaxed">{q.explanation}</p>
          </div>
        )}

        {answered && (
          <div className="text-right">
            <BrutalButton size="sm" onClick={handleNext}>
              {current + 1 >= QUIZ.length ? 'See Results' : 'Next Question'}
            </BrutalButton>
          </div>
        )}
      </BrutalCard>
    </section>
  );
}

function GlossaryItem({ term, def }) {
  const [open, setOpen] = useState(false);

  return (
    <button
      onClick={() => setOpen(!open)}
      className="w-full text-left p-3 border-2 border-ds-silver/20 hover:border-ds-silver/40 transition-colors"
    >
      <div className="flex items-center justify-between">
        <span className="font-grotesk font-bold text-sm text-ds-cyan">{term}</span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-ds-silver/40" />
        ) : (
          <ChevronDown className="w-4 h-4 text-ds-silver/40" />
        )}
      </div>
      {open && (
        <p className="mt-2 text-sm font-mono text-ds-silver/60 leading-relaxed">{def}</p>
      )}
    </button>
  );
}
