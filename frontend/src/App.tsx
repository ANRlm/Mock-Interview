import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { LoginPage } from '@/pages/LoginPage'
import { HomePage } from '@/pages/HomePage'
import { SetupPage } from '@/pages/SetupPage'
import { InterviewPage } from '@/pages/InterviewPage'
import { ReportPage } from '@/pages/ReportPage'
import { useAuthStore } from '@/stores/authStore'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<HomePage />} />
        <Route path="/setup" element={<ProtectedRoute><SetupPage /></ProtectedRoute>} />
        <Route path="/interview/:sessionId" element={<ProtectedRoute><InterviewPage /></ProtectedRoute>} />
        <Route path="/report/:sessionId" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
        <Route path="/report/latest" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
      </Routes>
    </AppShell>
  )
}