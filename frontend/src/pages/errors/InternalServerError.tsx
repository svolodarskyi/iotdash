import { ErrorPage } from '../../components/ErrorPage'

export function InternalServerError() {
  const handleReload = () => {
    window.location.reload()
  }

  return (
    <ErrorPage
      statusCode={500}
      title="Internal Server Error"
      message="Something went wrong on our end. Our team has been notified and is working on fixing the issue. Please try again in a few moments."
      showHomeLink
      showContactSupport
      customAction={
        <button
          onClick={handleReload}
          className="px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          🔄 Reload Page
        </button>
      }
    />
  )
}
