import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Github, Twitter, Mail } from 'lucide-react';

const TEAM = [
  'Alok', 'Rudranarayan', 'Shubham', 'Raj',
];

const FOOTER_LINKS = [
  { to: '/analyze', label: 'Analyze' },
  { to: '/history', label: 'History' },
  { to: '/learn', label: 'Learn' },
  { to: '/community', label: 'Community' },
];

export default function Footer() {
  return (
    <footer className="relative bg-ds-red border-t-3 border-ds-silver overflow-hidden">
      {/* Marquee */}
      <div className="overflow-hidden border-b-3 border-ds-silver/40 py-2">
        <div className="animate-marquee whitespace-nowrap flex">
          {Array.from({ length: 8 }).map((_, i) => (
            <span key={i} className="mx-8 text-sm font-mono text-white/80 uppercase tracking-widest">
              DEEPFAKE DETECTION • INDIA'S FIRST • MULTI-MODAL AI • TRUST VERIFICATION •
            </span>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-6 h-6 text-white" />
              <span className="font-grotesk font-black text-xl text-white tracking-tight">
                DEEP<span className="text-ds-bg">[</span>SCAN<span className="text-ds-bg">]</span>
              </span>
            </div>
            <p className="text-white/80 text-sm font-mono leading-relaxed">
              India's first multi-modal deepfake detection platform. Protecting truth in the age of
              synthetic media.
            </p>
            <div className="flex gap-3 mt-4">
              <a href="#" className="text-white/60 hover:text-white transition-colors" aria-label="GitHub">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-white/60 hover:text-white transition-colors" aria-label="Twitter">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-white/60 hover:text-white transition-colors" aria-label="Email">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-grotesk font-bold text-white text-sm uppercase tracking-wider mb-4">
              Navigation
            </h4>
            <ul className="space-y-2">
              {FOOTER_LINKS.map(({ to, label }) => (
                <li key={to}>
                  <Link
                    to={to}
                    className="text-white/70 hover:text-white text-sm font-mono transition-colors"
                  >
                    {'>'} {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Team */}
          <div>
            <h4 className="font-grotesk font-bold text-white text-sm uppercase tracking-wider mb-4">
              Team
            </h4>
            <div className="flex flex-wrap gap-2">
              {TEAM.map((name) => (
                <span
                  key={name}
                  className="px-2 py-1 bg-white/10 text-white text-xs font-mono border border-white/20"
                >
                  {name}
                </span>
              ))}
            </div>
            <p className="mt-4 text-white/60 text-xs font-mono">
              Team Bug Bytes • HackHive 2.0 • Datta Meghe College of Engineering, Airoli
            </p>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t-3 border-ds-silver/40 py-4 px-4 text-center">
        <p className="text-white/60 text-xs font-mono">
          © {new Date().getFullYear()} DeepScan • All rights reserved •{' '}
          <span className="text-white">Made in India 🇮🇳</span>
        </p>
      </div>
    </footer>
  );
}
