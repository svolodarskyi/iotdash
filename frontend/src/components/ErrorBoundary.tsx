import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { InternalServerError } from '../pages/errors/InternalServerError'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

/**
 * Error Boundary component to catch React rendering errors.
 *
 * Usage:
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 *
 * This will catch any errors in the component tree and display
 * a user-friendly error page instead of a blank screen.
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // Update state with error info
    this.setState({
      error,
      errorInfo,
    })

    // In production, you would send this to an error reporting service
    // Example: Sentry, LogRocket, etc.
    // logErrorToService(error, errorInfo)
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    })
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error page
      return (
        <div>
          <InternalServerError />

          {/* Development-only error details */}
          {import.meta.env.DEV && this.state.error && (
            <div className="fixed bottom-4 right-4 max-w-lg bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-red-900">Development Error Details</h3>
                <button
                  onClick={this.handleReset}
                  className="text-red-600 hover:text-red-800 font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                >
                  ✕
                </button>
              </div>
              <div className="text-sm text-red-800 space-y-2">
                <div>
                  <strong>Error:</strong>
                  <pre className="mt-1 p-2 bg-red-100 rounded text-xs overflow-auto max-h-32">
                    {this.state.error.toString()}
                  </pre>
                </div>
                {this.state.errorInfo && (
                  <div>
                    <strong>Component Stack:</strong>
                    <pre className="mt-1 p-2 bg-red-100 rounded text-xs overflow-auto max-h-32">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )
    }

    return this.props.children
  }
}
