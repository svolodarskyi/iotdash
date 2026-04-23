import { createFileRoute } from '@tanstack/react-router'
import { ForbiddenError } from '../pages/errors/ForbiddenError'

export const Route = createFileRoute('/403')({
  component: ForbiddenError,
})
