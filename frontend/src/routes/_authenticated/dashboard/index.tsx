import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useDevices } from '../../../hooks/useDevices'
import { useAdminDevices, useAdminOrgs, useDeviceTypes, useMetrics } from '../../../hooks/useAdmin'
import { useAuthStore } from '../../../store/authStore'
import { DeviceCard } from '../../../components/DeviceCard'

export const Route = createFileRoute('/_authenticated/dashboard/')({
  component: DashboardIndex,
})

function DashboardIndex() {
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
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">All Devices</h2>

      {/* Filters */}
      <div className="mb-4 flex gap-3">
        <select value={orgFilter} onChange={(e) => setOrgFilter(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md text-sm">
          <option value="">All organisations</option>
          {orgs?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
        </select>
        <select value={deviceTypeFilter} onChange={(e) => setDeviceTypeFilter(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md text-sm">
          <option value="">All device types</option>
          {deviceTypes?.map((dt) => <option key={dt.id} value={dt.id}>{dt.name}</option>)}
        </select>
        <select value={metricFilter} onChange={(e) => setMetricFilter(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-md text-sm">
          <option value="">All metrics</option>
          {metrics?.map((m) => <option key={m.id} value={m.name}>{m.name}{m.unit ? ` (${m.unit})` : ''}</option>)}
        </select>
      </div>

      {/* Devices table (read-only) */}
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
    </div>
  )
}
