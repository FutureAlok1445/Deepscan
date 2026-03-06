import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Shield, Scan } from 'lucide-react';
import useBackendStatus from '../../hooks/useBackendStatus';

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/analyze', label: 'Analyze' },
  { to: '/text-scan', label: 'Text Scan' },
  { to: '/history', label: 'History' },
  { to: '/learn', label: 'Learn' },
  { to: '/community', label: 'Community' },
];

export default function Navbar({ transparent = false }) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const { isOnline } = useBackendStatus(15000);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => setOpen(false), [location]);

  const showSolid = scrolled || !transparent;

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        showSolid
          ? 'bg-ds-bg/95 backdrop-blur-md border-b-3 border-ds-silver/20'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="relative">
              <Shield className="w-7 h-7 text-ds-red group-hover:rotate-12 transition-transform" />
              <Scan className="w-3 h-3 text-ds-cyan absolute -bottom-0.5 -right-0.5 animate-pulse" />
            </div>
            <span className="font-grotesk font-black text-xl tracking-tight">
              <span className="text-ds-silver">DEEP</span>
              <span className="text-ds-red">[</span>
              <span className="text-ds-silver">SCAN</span>
              <span className="text-ds-red">]</span>
            </span>
            {/* Backend status dot */}
            <span
              title={isOnline === null ? 'Checking backend...' : isOnline ? 'Backend online' : 'Backend offline'}
              className={`ml-2 inline-block w-2 h-2 rounded-full transition-colors ${
                isOnline === null ? 'bg-yellow-400 animate-pulse' : isOnline ? 'bg-green-400' : 'bg-red-500 animate-pulse'
              }`}
            />
          </Link>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`px-3 py-2 text-sm font-mono uppercase tracking-wider transition-colors ${
                  location.pathname === to
                    ? 'text-ds-red border-b-2 border-ds-red'
                    : 'text-ds-silver/70 hover:text-ds-silver'
                }`}
              >
                {label}
              </Link>
            ))}
            <Link
              to="/analyze"
              className="ml-4 px-4 py-2 bg-ds-red text-white font-grotesk font-bold text-sm uppercase border-3 border-ds-silver brutal-shadow hover:-translate-y-0.5 hover:shadow-brutal-lg transition-all"
            >
              Scan Now
            </Link>
          </div>

          {/* Mobile Toggle */}
          <button
            onClick={() => setOpen(!open)}
            className="md:hidden text-ds-silver p-2"
            aria-label="Toggle menu"
          >
            {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {open && (
        <div className="md:hidden bg-ds-bg border-t-3 border-ds-silver/20">
          <div className="px-4 py-4 space-y-2">
            {NAV_LINKS.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`block px-3 py-3 font-mono uppercase tracking-wider text-sm border-b border-ds-silver/20 ${
                  location.pathname === to ? 'text-ds-red' : 'text-ds-silver/70'
                }`}
              >
                {label}
              </Link>
            ))}
            <Link
              to="/analyze"
              className="block mt-3 px-4 py-3 bg-ds-red text-white font-grotesk font-bold text-sm text-center uppercase border-3 border-ds-silver brutal-shadow"
            >
              Scan Now
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
