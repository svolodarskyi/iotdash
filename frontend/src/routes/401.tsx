import { createFileRoute } from '@tanstack/react-router'
import { UnauthorizedError } from '../pages/errors/UnauthorizedError'

export const Route = createFileRoute('/401')({
  component: UnauthorizedError,
})
