import { createFileRoute } from '@tanstack/react-router'
import { InternalServerError } from '../pages/errors/InternalServerError'

export const Route = createFileRoute('/500')({
  component: InternalServerError,
})
