import { Link, useLocation } from '@tanstack/react-router'
import { useAuthStore } from '../store/authStore'

interface MobileNavProps {
  isOpen: boolean
  onClose: () => void
  onLogout: () => void
}

export function MobileNav({ isOpen, onClose, onLogout }: MobileNavProps) {
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  // Determine active route
  const isDashboard = location.pathname.startsWith('/dashboard')
  const isAdmin = location.pathname.startsWith('/admin')

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-20 z-40"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Slide-out menu */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-50 transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <span className="text-lg font-semibold text-gray-900">Menu</span>
            <button
              onClick={onClose}
              className="p-2 text-gray-500 hover:text-gray-700 min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="Close menu"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* User info */}
          {user && (
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <p className="text-sm font-medium text-gray-900">{user.full_name}</p>
              <p className="text-xs text-gray-600">{user.organisation_name}</p>
              <p className="text-xs text-gray-500 mt-1 capitalize">{user.role}</p>
            </div>
          )}

          {/* Navigation links */}
          <nav className="flex-1 p-4 space-y-2">
            <Link
              to="/dashboard"
              onClick={onClose}
              className={`block px-4 py-3 text-base rounded-md min-h-[44px] flex items-center transition-colors ${
                isDashboard
                  ? 'bg-blue-50 text-blue-700 font-semibold'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              Dashboard
            </Link>
            {user?.role === 'admin' && (
              <Link
                to="/admin"
                onClick={onClose}
                className={`block px-4 py-3 text-base rounded-md min-h-[44px] flex items-center transition-colors ${
                  isAdmin
                    ? 'bg-blue-50 text-blue-700 font-semibold'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Admin
              </Link>
            )}
          </nav>

          {/* Logout button */}
          <div className="p-4 border-t border-gray-200">
            <button
              onClick={() => {
                onClose()
                onLogout()
              }}
              className="w-full px-4 py-3 text-base text-red-600 hover:bg-red-50 rounded-md min-h-[44px] flex items-center justify-center"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
