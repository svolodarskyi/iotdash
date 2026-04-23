import { ErrorPage } from '../../components/ErrorPage'

export function ForbiddenError() {
  return (
    <ErrorPage
      statusCode={403}
      title="Access Denied"
      message="You don't have permission to access this resource. This page is restricted to administrators only. If you believe this is an error, please contact your system administrator."
      showContactSupport
    />
  )
}
