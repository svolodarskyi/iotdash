import { Link } from '@tanstack/react-router'

interface ErrorPageProps {
  statusCode: 401 | 403 | 404 | 500 | 503
  title: string
  message: string
  showHomeLink?: boolean
  showBackLink?: boolean
  showContactSupport?: boolean
  customAction?: React.ReactNode
}

const errorIcons = {
  401: '🔐',
  403: '🚫',
  404: '🔍',
  500: '⚠️',
  503: '🔧',
}

const errorColors = {
  401: 'text-yellow-600',
  403: 'text-red-600',
  404: 'text-blue-600',
  500: 'text-red-600',
  503: 'text-orange-600',
}

export function ErrorPage({
  statusCode,
  title,
  message,
  showHomeLink = true,
  showBackLink = true,
  showContactSupport = false,
  customAction,
}: ErrorPageProps) {
  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-lg font-semibold text-gray-900">IoT Dashboard</h1>
        </div>
      </div>

      {/* Error Content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          {/* Icon */}
          <div className="mb-2">
            <span className="text-4xl" role="img" aria-label={`Error ${statusCode}`}>
              {errorIcons[statusCode]}
            </span>
          </div>

        {/* Status Code */}
        <div className={`text-4xl font-bold mb-2 ${errorColors[statusCode]}`}>
          {statusCode}
        </div>

        {/* Title */}
        <h1 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">{title}</h1>

        {/* Message */}
        <p className="text-sm text-gray-600 mb-4 leading-relaxed">{message}</p>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {showBackLink && (
            <button
              onClick={() => window.history.back()}
              className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              ← Go Back
            </button>
          )}

          {showHomeLink && (
            <Link
              to="/dashboard"
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors min-h-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              Go to Home
            </Link>
          )}

          {customAction}
        </div>

        {/* Contact Support */}
        {showContactSupport && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Need help?{' '}
              <a
                href="mailto:support@iotdash.local"
                className="text-blue-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
              >
                Contact Support
              </a>
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-4 text-xs text-gray-400">
          <p>Error {statusCode} • {new Date().toLocaleTimeString()}</p>
        </div>
        </div>
      </div>
    </div>
  )
}
