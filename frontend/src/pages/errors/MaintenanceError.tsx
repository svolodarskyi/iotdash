import { ErrorPage } from '../../components/ErrorPage'

export function MaintenanceError() {
  const handleReload = () => {
    window.location.reload()
  }

  return (
    <ErrorPage
      statusCode={503}
      title="Under Maintenance"
      message="We're currently performing scheduled maintenance to improve your experience. The system will be back online shortly. Thank you for your patience."
      showBackLink={false}
      showHomeLink={false}
      customAction={
        <button
          onClick={handleReload}
          className="px-6 py-3 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          🔄 Check Again
        </button>
      }
    />
  )
}
