import { Routes, Route, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useState, useEffect } from 'react'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import Home from './pages/Home'
import Analyze from './pages/Analyze'
import Result from './pages/Result'
import History from './pages/History'
import Learn from './pages/Learn'
import Community from './pages/Community'
import TextAnalyze from './pages/TextAnalyze'

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
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/result/:id" element={<Result />} />
          <Route path="/history" element={<History />} />
          <Route path="/learn" element={<Learn />} />
          <Route path="/community" element={<Community />} />
          <Route path="/analyze/text" element={<TextAnalyze />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
