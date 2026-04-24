import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { getExternalServices } from '../../../lib/api'

export const Route = createFileRoute('/_authenticated/admin/')({
  component: AdminDashboard,
})

function AdminDashboard() {
  const { data: externalServices, isLoading: servicesLoading } = useQuery({
    queryKey: ['external-services'],
    queryFn: getExternalServices,
  })

  const sections = [
    {
      title: 'Organisations',
      description: 'Manage client organisations',
      to: '/admin/organisations' as const,
    },
    {
      title: 'Users',
      description: 'Manage user accounts and roles',
      to: '/admin/users' as const,
    },
    {
      title: 'Devices',
      description: 'Provision and configure IoT devices',
      to: '/admin/devices' as const,
    },
  ]

  const externalLinks = [
    {
      title: 'Grafana',
      description: 'View dashboards and alerts',
      url: externalServices?.grafana_url,
      icon: '/grafana-logo.svg',
    },
    {
      title: 'InfluxDB',
      description: 'Query time-series data',
      url: externalServices?.influxdb_url,
      icon: '/influxdb-logo.svg',
    },
    {
      title: 'EMQX',
      description: 'Monitor MQTT broker',
      url: externalServices?.emqx_url,
      icon: '/emqx-logo.svg',
    },
  ]

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Admin Panel</h1>

      {/* Management Sections */}
      <div className="mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Management</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {sections.map((s) => (
            <Link
              key={s.to}
              to={s.to}
              className="block p-6 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              <h3 className="text-lg font-medium text-gray-900 mb-2">{s.title}</h3>
              <p className="text-sm text-gray-500">{s.description}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* External Services */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">External Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {servicesLoading ? (
            <p className="text-gray-500 col-span-3">Loading services...</p>
          ) : (
            externalLinks.map((link) => (
              <a
                key={link.title}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-6 bg-white rounded-lg border border-gray-200 hover:border-green-300 hover:shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
              >
                <div className="flex items-center gap-3 mb-2">
                  <img src={link.icon} alt={`${link.title} logo`} className="w-8 h-8" />
                  <h3 className="text-lg font-medium text-gray-900">{link.title}</h3>
                </div>
                <p className="text-sm text-gray-500">{link.description}</p>
              </a>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
