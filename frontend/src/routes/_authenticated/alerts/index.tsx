import { createFileRoute, Link } from '@tanstack/react-router'
import { useAlerts, useDeleteAlert, useToggleAlert } from '../../../hooks/useAlerts'
import { useState } from 'react'

export const Route = createFileRoute('/_authenticated/alerts/')({
  component: AlertsIndex,
})

function AlertsIndex() {
  const { data: alerts, isLoading, error } = useAlerts()
  const toggleAlert = useToggleAlert()
  const deleteAlert = useDeleteAlert()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  if (isLoading) {
    return <p className="text-gray-500">Loading alerts...</p>
  }

  if (error) {
    return <p className="text-red-600">Failed to load alerts: {error.message}</p>
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

  const formatDuration = (seconds: number) => {
    if (seconds >= 3600) return `${Math.floor(seconds / 3600)}h`
    if (seconds >= 60) return `${Math.floor(seconds / 60)}m`
    return `${seconds}s`
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Alerts</h2>
        <Link
          to="/alerts/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
        >
          New Alert
        </Link>
      </div>

      {!alerts?.length ? (
        <p className="text-gray-500">
          No alerts configured. Create one to get notified when device metrics
          exceed thresholds.
        </p>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
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
