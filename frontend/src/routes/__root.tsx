import { createRootRoute, Outlet } from '@tanstack/react-router'
import { Layout } from '../components/Layout'
import { useMe } from '../hooks/useAuth'

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  useMe()

  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}
