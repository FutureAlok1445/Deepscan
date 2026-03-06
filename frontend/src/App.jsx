import { Routes, Route, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useState, useEffect, lazy, Suspense } from 'react'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Home from './pages/Home'

// Lazy-loaded pages for faster initial load
const Analyze = lazy(() => import('./pages/Analyze'))
const Result = lazy(() => import('./pages/Result'))
const History = lazy(() => import('./pages/History'))
const Learn = lazy(() => import('./pages/Learn'))
const Community = lazy(() => import('./pages/Community'))
const TextScan = lazy(() => import('./pages/TextScan'))

function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-3 border-ds-red border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="font-mono text-xs text-ds-silver/40">Loading...</p>
      </div>
    </div>
  )
}

function ScrollProgress() {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const onScroll = () => {
      const scrollTop = document.documentElement.scrollTop
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight
      setWidth(scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0)
    }
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, height: 3,
      width: width + '%', background: '#ff3c00',
      zIndex: 9999, transition: 'width 0.1s linear',
    }} />
  )
}

export default function App() {
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--silver)', fontFamily: 'var(--font-heading)' }}>
      <ScrollProgress />
      <Toaster position="top-right" toastOptions={{
        style: {
          background: '#0f0f1a',
          color: '#e0e0e0',
          border: '2px solid #ff3c00',
          fontFamily: "'Space Mono', monospace",
          fontSize: '0.8rem',
        },
      }} />
      <Navbar transparent={isHome} />
      <main style={{ paddingTop: isHome ? 0 : 64 }}>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/result/:id" element={<Result />} />
            <Route path="/history" element={<History />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/community" element={<Community />} />
            <Route path="/text-scan" element={<TextScan />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}
