import { createFileRoute } from '@tanstack/react-router'
import { MaintenanceError } from '../pages/errors/MaintenanceError'

export const Route = createFileRoute('/503')({
  component: MaintenanceError,
})
