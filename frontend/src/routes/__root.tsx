import { createRootRoute, Outlet, useLocation } from '@tanstack/react-router'
import { Layout } from '../components/Layout'
import { useMe } from '../hooks/useAuth'

export const Route = createRootRoute({
  component: RootComponent,
})

function RootComponent() {
  const location = useLocation()
  const isLoginPage = location.pathname === '/login'

  // Only fetch user data when not on login page
  useMe({ enabled: !isLoginPage })

  return (
    <Layout>
      <Outlet />
    </Layout>
  )
}
