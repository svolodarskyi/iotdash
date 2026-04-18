import type { ReactNode } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { useAuthStore } from '../store/authStore'
import { useLogout } from '../hooks/useAuth'

export function Layout({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const logout = useLogout()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSuccess: () => {
        navigate({ to: '/login' })
      },
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="text-xl font-semibold text-gray-900">
              IoT Dashboard
            </Link>
            {isAuthenticated && (
              <nav className="flex items-center gap-4">
                <Link
                  to="/dashboard"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Devices
                </Link>
                <Link
                  to="/alerts"
                  className="text-sm text-gray-600 hover:text-gray-900"
                >
                  Alerts
                </Link>
                {user?.role === 'admin' && (
                  <Link
                    to="/admin"
                    className="text-sm text-gray-600 hover:text-gray-900"
                  >
                    Admin
                  </Link>
                )}
              </nav>
            )}
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated && user ? (
              <>
                <span className="text-sm text-gray-600">
                  {user.full_name} — {user.organisation_name}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Logout
                </button>
              </>
            ) : (
              <span className="text-sm text-gray-500">v0.1.0</span>
            )}
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </div>
  )
}
