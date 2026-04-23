import { createFileRoute } from '@tanstack/react-router'
import { NotFoundError } from '../pages/errors/NotFoundError'

export const Route = createFileRoute('/404')({
  component: NotFoundError,
})
