import type { ReactNode } from 'react'
import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from '@tanstack/react-router'
import { useAuthStore } from '../store/authStore'
import { useLogout } from '../hooks/useAuth'
import { useIsMobile } from '../hooks/useMediaQuery'
import { MobileNav } from './MobileNav'

export function Layout({ children }: { children: ReactNode }) {
  const user = useAuthStore((s) => s.user)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const logout = useLogout()
  const navigate = useNavigate()
  const location = useLocation()
  const isMobile = useIsMobile()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Determine active route
  const isDashboard = location.pathname.startsWith('/dashboard')
  const isAdmin = location.pathname.startsWith('/admin')

  // Close mobile menu when viewport changes to desktop
  useEffect(() => {
    if (!isMobile && mobileMenuOpen) {
      setMobileMenuOpen(false)
    }
  }, [isMobile, mobileMenuOpen])

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    // Cleanup on unmount
    return () => {
      document.body.style.overflow = ''
    }
  }, [mobileMenuOpen])

  const handleLogout = () => {
    logout.mutate(undefined, {
      onSuccess: () => {
        navigate({ to: '/login' })
      },
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-4 md:px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Hamburger menu button (mobile only) */}
            {isMobile && isAuthenticated && (
              <button
                onClick={() => setMobileMenuOpen(true)}
                className="p-2 text-gray-600 hover:text-gray-900 min-h-[44px] min-w-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                aria-label="Open menu"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
            )}

            <Link to="/dashboard" className="text-xl font-semibold text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
              IoT Dashboard
            </Link>

            {/* Desktop navigation */}
            {isAuthenticated && !isMobile && (
              <nav className="flex items-center gap-4">
                <Link
                  to="/dashboard"
                  className={`text-sm hover:text-gray-900 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${
                    isDashboard
                      ? 'text-blue-600 font-semibold'
                      : 'text-gray-600'
                  }`}
                >
                  Dashboard
                </Link>
                {user?.role === 'admin' && (
                  <Link
                    to="/admin"
                    className={`text-sm hover:text-gray-900 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${
                      isAdmin
                        ? 'text-blue-600 font-semibold'
                        : 'text-gray-600'
                    }`}
                  >
                    Admin
                  </Link>
                )}
              </nav>
            )}
          </div>

          {/* Desktop user info and logout */}
          <div className="flex items-center gap-4">
            {isAuthenticated && user && !isMobile ? (
              <>
                <span className="text-sm text-gray-600 hidden sm:inline">
                  {user.full_name} — {user.organisation_name}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-500 hover:text-gray-700 min-h-[44px] px-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                >
                  Logout
                </button>
              </>
            ) : !isAuthenticated ? (
              <span className="text-sm text-gray-500">v0.1.0</span>
            ) : null}
          </div>
        </div>
      </header>

      {/* Mobile navigation */}
      {isMobile && isAuthenticated && (
        <MobileNav
          isOpen={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          onLogout={handleLogout}
        />
      )}

      <main className="max-w-7xl mx-auto px-4 md:px-6 py-6 md:py-8">{children}</main>
    </div>
  )
}
