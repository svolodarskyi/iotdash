import type { ReactNode } from 'react'
import { Link } from '@tanstack/react-router'

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/dashboard" className="text-xl font-semibold text-gray-900">
            IoT Dashboard
          </Link>
          <span className="text-sm text-gray-500">v0.1.0</span>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </div>
  )
}
