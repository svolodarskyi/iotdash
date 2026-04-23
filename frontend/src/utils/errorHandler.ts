import { useNavigate } from '@tanstack/react-router'

/**
 * Error handler utility for API errors.
 * Maps HTTP status codes to appropriate error pages.
 */

export interface ApiError extends Error {
  status?: number
  statusText?: string
}

/**
 * Handle API errors and redirect to appropriate error pages.
 *
 * @param error - The error object from the API call
 * @param navigate - TanStack Router navigate function
 */
export function handleApiError(error: unknown, navigate?: ReturnType<typeof useNavigate>) {
  // If error is a Response object
  if (error instanceof Response) {
    const status = error.status

    // Map status codes to error pages
    switch (status) {
      case 401:
        navigate?.({ to: '/401' })
        break
      case 403:
        navigate?.({ to: '/403' })
        break
      case 404:
        navigate?.({ to: '/404' })
        break
      case 500:
        navigate?.({ to: '/500' })
        break
      case 503:
        navigate?.({ to: '/503' })
        break
      default:
        // For other errors, log and optionally redirect to 500
        console.error('Unhandled API error:', error)
        if (status >= 500) {
          navigate?.({ to: '/500' })
        }
    }

    return
  }

  // If error is a custom ApiError with status
  if (error && typeof error === 'object' && 'status' in error) {
    const apiError = error as ApiError
    const status = apiError.status

    switch (status) {
      case 401:
        navigate?.({ to: '/401' })
        break
      case 403:
        navigate?.({ to: '/403' })
        break
      case 404:
        navigate?.({ to: '/404' })
        break
      case 500:
        navigate?.({ to: '/500' })
        break
      case 503:
        navigate?.({ to: '/503' })
        break
      default:
        console.error('Unhandled API error:', error)
        if (status && status >= 500) {
          navigate?.({ to: '/500' })
        }
    }

    return
  }

  // If error is a string from our apiFetch helper
  if (error instanceof Error && error.message.includes('API error:')) {
    const match = error.message.match(/API error: (\d+)/)
    if (match) {
      const status = parseInt(match[1], 10)
      switch (status) {
        case 401:
          navigate?.({ to: '/401' })
          break
        case 403:
          navigate?.({ to: '/403' })
          break
        case 404:
          navigate?.({ to: '/404' })
          break
        case 500:
          navigate?.({ to: '/500' })
          break
        case 503:
          navigate?.({ to: '/503' })
          break
        default:
          if (status >= 500) {
            navigate?.({ to: '/500' })
          }
      }
    }
  }

  // Generic error handling
  console.error('Unhandled error:', error)
}

/**
 * Extract status code from error message.
 * Used for errors thrown by apiFetch helper.
 */
export function getErrorStatus(error: unknown): number | null {
  if (error instanceof Error && error.message.includes('API error:')) {
    const match = error.message.match(/API error: (\d+)/)
    if (match) {
      return parseInt(match[1], 10)
    }
  }
  return null
}

/**
 * Check if error is a specific HTTP status code.
 */
export function isErrorStatus(error: unknown, status: number): boolean {
  const errorStatus = getErrorStatus(error)
  return errorStatus === status
}

/**
 * Hook to get error handler with navigation.
 */
export function useErrorHandler() {
  const navigate = useNavigate()

  return (error: unknown) => {
    handleApiError(error, navigate)
  }
}
