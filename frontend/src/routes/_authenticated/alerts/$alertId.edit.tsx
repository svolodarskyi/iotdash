import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { useAlert, useUpdateAlert } from '../../../hooks/useAlerts'
import { useDeviceMetrics } from '../../../hooks/useDevices'

export const Route = createFileRoute('/_authenticated/alerts/$alertId/edit')({
  component: EditAlert,
})

function EditAlert() {
  const { alertId } = Route.useParams()
  const navigate = useNavigate()
  const { data: alert, isLoading, error } = useAlert(alertId)
  const updateAlert = useUpdateAlert()

  const [metric, setMetric] = useState('')
  const [condition, setCondition] = useState('')
  const [threshold, setThreshold] = useState('')
  const [durationSeconds, setDurationSeconds] = useState('')
  const [email, setEmail] = useState('')
  const [initialized, setInitialized] = useState(false)

  const { data: deviceMetrics } = useDeviceMetrics(alert?.device_id)

  useEffect(() => {
    if (alert && !initialized) {
      setMetric(alert.metric)
      setCondition(alert.condition)
      setThreshold(String(alert.threshold))
      setDurationSeconds(String(alert.duration_seconds))
      setEmail(alert.notification_email ?? '')
      setInitialized(true)
    }
  }, [alert, initialized])

  if (isLoading) {
    return <p className="text-gray-500">Loading alert...</p>
  }

  if (error || !alert) {
    return <p className="text-red-600">Alert not found.</p>
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    updateAlert.mutate(
      {
        id: alertId,
        body: {
          metric,
          condition,
          threshold: parseFloat(threshold),
          duration_seconds: parseInt(durationSeconds, 10),
          notification_email: email,
        },
      },
      {
        onSuccess: () => navigate({ to: '/alerts' }),
      },
    )
  }

  return (
    <div className="max-w-lg">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Edit Alert</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Device
          </label>
          <input
            type="text"
            value={alert.device_code}
            disabled
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm bg-gray-50 text-gray-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Device cannot be changed on an existing alert.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Metric
          </label>
          {deviceMetrics?.length ? (
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {deviceMetrics.map((dm) => (
                <option key={dm.metric_id} value={dm.metric_name}>
                  {dm.metric_name}{dm.metric_unit ? ` (${dm.metric_unit})` : ''}
                </option>
              ))}
            </select>
          ) : (
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value={alert.metric}>{alert.metric}</option>
            </select>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Condition
            </label>
            <select
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="above">Above</option>
              <option value="below">Below</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Threshold
            </label>
            <input
              type="number"
              step="0.1"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Duration (seconds)
          </label>
          <input
            type="number"
            min="10"
            value={durationSeconds}
            onChange={(e) => setDurationSeconds(e.target.value)}
            required
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">
            Alert fires after the condition holds for this many seconds.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notification Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          />
        </div>

        {updateAlert.isError && (
          <p className="text-sm text-red-600">
            Failed to update alert: {updateAlert.error.message}
          </p>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={updateAlert.isPending}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            {updateAlert.isPending ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            type="button"
            onClick={() => navigate({ to: '/alerts' })}
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
