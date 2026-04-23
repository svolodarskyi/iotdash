import { ErrorPage } from '../../components/ErrorPage'

export function NotFoundError() {
  return (
    <ErrorPage
      statusCode={404}
      title="Page Not Found"
      message="The page you're looking for doesn't exist. It may have been moved, deleted, or the URL might be incorrect. Please check the address and try again."
      showBackLink
      showHomeLink
    />
  )
}
