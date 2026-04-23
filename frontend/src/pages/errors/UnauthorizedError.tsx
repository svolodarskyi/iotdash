import { Link } from '@tanstack/react-router'
import { ErrorPage } from '../../components/ErrorPage'

export function UnauthorizedError() {
  return (
    <ErrorPage
      statusCode={401}
      title="Authentication Required"
      message="You need to be logged in to access this page. Please sign in with your credentials to continue."
      showBackLink={false}
      customAction={
        <Link
          to="/login"
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors min-h-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          Sign In
        </Link>
      }
    />
  )
}
