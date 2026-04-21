import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useDevices } from '../../../hooks/useDevices'
import { useAdminDevices, useAdminOrgs, useDeviceTypes, useMetrics } from '../../../hooks/useAdmin'
import { useAlerts, useDeleteAlert, useToggleAlert } from '../../../hooks/useAlerts'
import { useAuthStore } from '../../../store/authStore'
import { DeviceCard } from '../../../components/DeviceCard'
import { useIsMobile } from '../../../hooks/useMediaQuery'

export const Route = createFileRoute('/_authenticated/dashboard/')({
  component: DashboardIndex,
})

type Tab = 'devices' | 'alerts'

function DashboardIndex() {
  const [activeTab, setActiveTab] = useState<Tab>('devices')

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h2>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-4" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('devices')}
            className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors min-h-[44px] ${
              activeTab === 'devices'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Devices
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors min-h-[44px] ${
              activeTab === 'alerts'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Alerts
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'devices' ? <DevicesTab /> : <AlertsTab />}
    </div>
  )
}

function DevicesTab() {
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  if (isAdmin) {
    return <AdminDevicesView />
  }
  return <ViewerDevicesView />
}

function ViewerDevicesView() {
  const { data: devices, isLoading, error } = useDevices()

  if (isLoading) {
    return <p className="text-gray-500">Loading devices...</p>
  }

  if (error) {
    return <p className="text-red-600">Failed to load devices: {error.message}</p>
  }

  if (!devices?.length) {
    return <p className="text-gray-500">No devices found.</p>
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Devices</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map((device) => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </div>
    </div>
  )
}

function AdminDevicesView() {
  const isMobile = useIsMobile()
  const [orgFilter, setOrgFilter] = useState<string>('')
  const [deviceTypeFilter, setDeviceTypeFilter] = useState<string>('')
  const [metricFilter, setMetricFilter] = useState<string>('')

  const { data: orgs } = useAdminOrgs()
  const { data: devices, isLoading } = useAdminDevices(
    orgFilter || undefined,
    deviceTypeFilter || undefined,
    metricFilter || undefined,
  )
  const { data: deviceTypes } = useDeviceTypes()
  const { data: metrics } = useMetrics()

  if (isLoading) {
    return <p className="text-gray-500">Loading devices...</p>
  }

  return (
    <div>
      {/* Filters */}
      <div className="mb-4 flex flex-col md:flex-row gap-3">
        <select
          value={orgFilter}
          onChange={(e) => setOrgFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px]"
        >
          <option value="">All organisations</option>
          {orgs?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
        </select>
        <select
          value={deviceTypeFilter}
          onChange={(e) => setDeviceTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px]"
        >
          <option value="">All device types</option>
          {deviceTypes?.map((dt) => <option key={dt.id} value={dt.id}>{dt.name}</option>)}
        </select>
        <select
          value={metricFilter}
          onChange={(e) => setMetricFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px]"
        >
          <option value="">All metrics</option>
          {metrics?.map((m) => <option key={m.id} value={m.name}>{m.name}{m.unit ? ` (${m.unit})` : ''}</option>)}
        </select>
      </div>

      {/* Devices - responsive cards on mobile, table on desktop */}
      {isMobile ? (
        // Mobile card view
        <div className="space-y-3">
          {devices?.map((d) => (
            <div key={d.id} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{d.name}</h3>
                  <p className="text-sm text-gray-600 font-mono">{d.device_code}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  d.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {d.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="space-y-2 mb-3">
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Org:</span> {d.organisation_name}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Type:</span> {d.device_type_name}
                </p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {d.metrics.filter((m) => m.is_enabled).map((m) => (
                    <span key={m.metric_id} className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      {m.metric_name}
                    </span>
                  ))}
                  {!d.metrics.filter((m) => m.is_enabled).length && (
                    <span className="text-gray-400 text-xs">No metrics</span>
                  )}
                </div>
              </div>

              <Link
                to="/dashboard/$deviceId"
                params={{ deviceId: d.id }}
                className="w-full px-4 py-2 text-center text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 min-h-[44px] flex items-center justify-center"
              >
                View Dashboard
              </Link>
            </div>
          ))}
          {!devices?.length && (
            <div className="bg-white p-8 rounded-lg border border-gray-200 text-center text-gray-500">
              No devices found.
            </div>
          )}
        </div>
      ) : (
        // Desktop table view
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">UID</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Organisation</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Metrics</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Active</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">View</th>
              </tr>
            </thead>
            <tbody>
              {devices?.map((d) => (
                <tr key={d.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-3 font-mono text-gray-900">{d.device_code}</td>
                  <td className="px-4 py-3 text-gray-700">{d.name}</td>
                  <td className="px-4 py-3 text-gray-500">{d.organisation_name}</td>
                  <td className="px-4 py-3 text-gray-500">{d.device_type_name}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {d.metrics.filter((m) => m.is_enabled).map((m) => (
                        <span key={m.metric_id} className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                          {m.metric_name}
                        </span>
                      ))}
                      {!d.metrics.filter((m) => m.is_enabled).length && (
                        <span className="text-gray-400 text-xs">none</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium ${d.is_active ? 'text-green-600' : 'text-red-500'}`}>
                      {d.is_active ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to="/dashboard/$deviceId"
                      params={{ deviceId: d.id }}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Dashboard
                    </Link>
                  </td>
                </tr>
              ))}
              {!devices?.length && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No devices found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function AlertsTab() {
  const isMobile = useIsMobile()
  const { data: alerts, isLoading, error } = useAlerts()
  const toggleAlert = useToggleAlert()
  const deleteAlert = useDeleteAlert()
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [openCardMenu, setOpenCardMenu] = useState<string | null>(null)
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const formatDuration = (seconds: number) => {
    if (seconds >= 3600) return `${Math.floor(seconds / 3600)}h`
    if (seconds >= 60) return `${Math.floor(seconds / 60)}m`
    return `${seconds}s`
  }

  const handleDelete = (id: string) => {
    if (!confirm('Are you sure you want to delete this alert?')) return
    setDeletingId(id)
    deleteAlert.mutate(id, {
      onSettled: () => setDeletingId(null),
    })
  }

  const handleToggle = (id: string, currentEnabled: boolean) => {
    toggleAlert.mutate({ id, body: { is_enabled: !currentEnabled } })
  }

  if (isLoading) {
    return <p className="text-gray-500">Loading alerts...</p>
  }

  if (error) {
    return <p className="text-red-600">Failed to load alerts: {error.message}</p>
  }

  if (!alerts?.length) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">
          {isAdmin
            ? 'No alerts configured across any organisation.'
            : 'No alerts configured. Create one to get notified when device metrics exceed thresholds.'}
        </p>
        <Link
          to="/alerts/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 min-h-[44px]"
        >
          Create Alert
        </Link>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Link
          to="/alerts/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 min-h-[44px] flex items-center"
        >
          {isMobile ? 'New' : 'New Alert'}
        </Link>
      </div>

      {isMobile ? (
        // Mobile card view
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div key={alert.id} className="bg-white p-4 rounded-lg border border-gray-200 shadow">
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{alert.device_code}</h3>
                  {isAdmin && (
                    <p className="text-xs text-gray-500">{alert.organisation_name}</p>
                  )}
                  <p className="text-sm text-gray-700 mt-1">
                    {alert.metric} {alert.condition} {alert.threshold}
                  </p>
                </div>
                <button
                  onClick={() => setOpenCardMenu(openCardMenu === alert.id ? null : alert.id)}
                  className="p-2 text-gray-500 hover:text-gray-700 min-h-[44px] min-w-[44px] flex items-center justify-center"
                  aria-label="Actions"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Duration:</span>
                  <span className="text-gray-900">{formatDuration(alert.duration_seconds)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Email:</span>
                  <span className="text-gray-900 truncate ml-2 text-xs">{alert.notification_email}</span>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                  <span className="text-gray-600">Status:</span>
                  <button
                    onClick={() => handleToggle(alert.id, alert.is_enabled)}
                    disabled={toggleAlert.isPending}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      alert.is_enabled ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        alert.is_enabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {openCardMenu === alert.id && (
                <div className="pt-3 border-t border-gray-200 space-y-2 mt-3">
                  <Link
                    to="/alerts/$alertId/edit"
                    params={{ alertId: alert.id }}
                    onClick={() => setOpenCardMenu(null)}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 rounded min-h-[44px] flex items-center"
                  >
                    Edit Alert
                  </Link>
                  <button
                    onClick={() => {
                      handleDelete(alert.id)
                      setOpenCardMenu(null)
                    }}
                    disabled={deletingId === alert.id}
                    className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded min-h-[44px] flex items-center disabled:opacity-50"
                  >
                    {deletingId === alert.id ? 'Deleting Alert...' : 'Delete Alert'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        // Desktop table view
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {isAdmin && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organisation
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Device
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Condition
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Enabled
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {alerts.map((alert) => (
                <tr key={alert.id}>
                  {isAdmin && (
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {alert.organisation_name}
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {alert.device_code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {alert.metric} {alert.condition} {alert.threshold}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDuration(alert.duration_seconds)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {alert.notification_email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button
                      onClick={() => handleToggle(alert.id, alert.is_enabled)}
                      disabled={toggleAlert.isPending}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        alert.is_enabled ? 'bg-blue-600' : 'bg-gray-200'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          alert.is_enabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <Link
                      to="/alerts/$alertId/edit"
                      params={{ alertId: alert.id }}
                      className="text-blue-600 hover:text-blue-800 mr-3"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(alert.id)}
                      disabled={deletingId === alert.id}
                      className="text-red-600 hover:text-red-800"
                    >
                      {deletingId === alert.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
