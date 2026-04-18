import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'
import { useAuthStore } from '../../store/authStore'

export const Route = createFileRoute('/_authenticated/admin')({
  beforeLoad: () => {
    const { user } = useAuthStore.getState()
    if (user?.role !== 'admin') {
      throw redirect({ to: '/dashboard' })
    }
  },
  component: AdminLayout,
})

function AdminLayout() {
  return <Outlet />
}
