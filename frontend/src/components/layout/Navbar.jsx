import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Shield, Scan, Globe, Search, ChevronDown } from 'lucide-react';
import useBackendStatus from '../../hooks/useBackendStatus';

const NAV_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/analyze', label: 'Analyze' },
  { to: '/analyze/text', label: 'Text Scan' },
  { to: '/history', label: 'History' },
  { to: '/learn', label: 'Learn' },
  { to: '/community', label: 'Community' },
];

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi' },
  { code: 'mr', name: 'Marathi' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'zh-CN', name: 'Chinese (Simplified)' },
  { code: 'ru', name: 'Russian' },
  { code: 'ar', name: 'Arabic' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'bn', name: 'Bengali' },
  { code: 'gu', name: 'Gujarati' },
  { code: 'kn', name: 'Kannada' },
  { code: 'ml', name: 'Malayalam' },
  { code: 'pa', name: 'Punjabi' },
  { code: 'ta', name: 'Tamil' },
  { code: 'te', name: 'Telugu' },
  { code: 'ur', name: 'Urdu' },
  { code: 'nl', name: 'Dutch' },
  { code: 'tr', name: 'Turkish' },
  { code: 'vi', name: 'Vietnamese' },
  { code: 'th', name: 'Thai' },
  { code: 'id', name: 'Indonesian' },
];

function LanguageSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [activeLang, setActiveLang] = useState('en');
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const changeLanguage = (code) => {
    try {
      // 1. Set the cookie - this is the most reliable way google translate tracks state
      // format: /origin_lang/target_lang
      const cookieValue = `/en/${code}`;
      document.cookie = `googtrans=${cookieValue}; path=/`;
      document.cookie = `googtrans=${cookieValue}; path=/; domain=${window.location.hostname}`;
      
      // 2. Try to find the combo and trigger it for instant change
      const googleCombo = document.querySelector('.goog-te-combo');
      if (googleCombo) {
        googleCombo.value = code;
        googleCombo.dispatchEvent(new Event('change'));
        setActiveLang(code);
      } else {
        // 3. Fallback: If combo isn't there, we need a reload to pick up the cookie
        window.location.reload();
      }
      
      setActiveLang(code);
    } catch (err) {
      console.error("Language change failed:", err);
    }
    setIsOpen(false);
    setSearch('');
  };

  const filteredLangs = LANGUAGES.filter(l => 
    l.name.toLowerCase().includes(search.toLowerCase()) || 
    l.code.toLowerCase().includes(search.toLowerCase())
  );

  const currentLangName = LANGUAGES.find(l => l.code === activeLang)?.name || 'English';

  return (
    <div className="lang-selector-container px-2" ref={dropdownRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 border-2 border-ds-silver/20 hover:border-ds-red transition-all group outline-none"
      >
        <Globe className="w-3.5 h-3.5 text-ds-silver/60 group-hover:text-ds-red" />
        <span className="text-[10px] font-mono uppercase tracking-widest text-ds-silver">
          {currentLangName}
        </span>
        <ChevronDown className={`w-3 h-3 text-ds-silver/40 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="lang-dropdown absolute top-full right-0 mt-2">
          <div className="lang-search-wrapper flex items-center gap-2 bg-ds-bg/50">
            <Search className="w-3.5 h-3.5 text-ds-silver/30" />
            <input 
              type="text" 
              placeholder="Search language..."
              className="lang-search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
          <div className="lang-list">
            {filteredLangs.map(lang => (
              <div
                key={lang.code}
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  changeLanguage(lang.code);
                }}
                className={`lang-item ${activeLang === lang.code ? 'active' : ''}`}
              >
                {lang.name}
              </div>
            ))}
            {filteredLangs.length === 0 && (
              <div className="p-4 text-center text-[10px] font-mono text-ds-silver/30 uppercase">
                No results found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Navbar({ transparent = false }) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    // 1. Script injection
    if (!document.getElementById('google-translate-script')) {
      const script = document.createElement('script');
      script.id = 'google-translate-script';
      script.src = "https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
      script.async = true;
      document.body.appendChild(script);

      window.googleTranslateElementInit = () => {
        if (window.google && window.google.translate) {
          new window.google.translate.TranslateElement({
            pageLanguage: 'en',
            autoDisplay: false,
          }, 'google_translate_hidden');
        }
      };
    }
    
    // 2. Sync activeLang from cookie if it exists
    const match = document.cookie.match(/googtrans=\/en\/([^;]+)/);
    if (match && match[1]) {
      // Logic to find state-sync here if needed
    }

    setOpen(false);
  }, [location]);

  const showSolid = scrolled || !transparent;

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${showSolid
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
          </Link>

          {/* Hidden Google Container (Off-screen but NOT display:none for engine to work) */}
          <div id="google_translate_hidden" className="fixed -top-[500px] -left-[500px] opacity-0 pointer-events-none"></div>

          {/* Desktop Links */}
          <div className="hidden lg:flex items-center gap-1">
            {NAV_LINKS.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`px-3 py-2 text-sm font-mono uppercase tracking-wider transition-colors ${location.pathname === to
                    ? 'text-ds-red border-b-2 border-ds-red'
                    : 'text-ds-silver/70 hover:text-ds-silver'
                  }`}
              >
                {label}
              </Link>
            ))}

            <LanguageSelector />

            <Link
              to="/analyze"
              className="ml-2 px-4 py-2 bg-ds-red text-white font-grotesk font-bold text-sm uppercase border-3 border-ds-silver brutal-shadow hover:-translate-y-0.5 hover:shadow-brutal-lg transition-all"
            >
              Scan Now
            </Link>
          </div>

          {/* Mobile Toggle & Simplified Mobile selector */}
          <div className="flex items-center gap-2 lg:hidden">
            <LanguageSelector />
            <button
              onClick={() => setOpen(!open)}
              className="text-ds-silver p-2"
              aria-label="Toggle menu"
            >
              {open ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {open && (
        <div className="lg:hidden bg-ds-bg border-t-3 border-ds-silver/20">
          <div className="px-4 py-4 space-y-2">
            {NAV_LINKS.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`block px-3 py-3 font-mono uppercase tracking-wider text-sm border-b border-ds-silver/20 ${location.pathname === to ? 'text-ds-red' : 'text-ds-silver/70'
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

