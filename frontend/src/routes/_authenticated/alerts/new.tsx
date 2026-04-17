import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useDevices } from '../../../hooks/useDevices'
import { useCreateAlert } from '../../../hooks/useAlerts'
import { useAuthStore } from '../../../store/authStore'

export const Route = createFileRoute('/_authenticated/alerts/new')({
  component: NewAlert,
})

function NewAlert() {
  const navigate = useNavigate()
  const { data: devices, isLoading: devicesLoading } = useDevices()
  const createAlert = useCreateAlert()
  const user = useAuthStore((s) => s.user)

  const [deviceId, setDeviceId] = useState('')
  const [metric, setMetric] = useState('temperature')
  const [condition, setCondition] = useState('above')
  const [threshold, setThreshold] = useState('30')
  const [durationSeconds, setDurationSeconds] = useState('60')
  const [email, setEmail] = useState(user?.email ?? '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createAlert.mutate(
      {
        device_id: deviceId,
        metric,
        condition,
        threshold: parseFloat(threshold),
        duration_seconds: parseInt(durationSeconds, 10),
        notification_email: email,
      },
      {
        onSuccess: () => navigate({ to: '/alerts' }),
      },
    )
  }

  return (
    <div className="max-w-lg">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">New Alert</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Device
          </label>
          {devicesLoading ? (
            <p className="text-sm text-gray-500">Loading devices...</p>
          ) : (
            <select
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="">Select a device</option>
              {devices?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.device_code})
                </option>
              ))}
            </select>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Metric
          </label>
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="temperature">Temperature</option>
          </select>
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

        {createAlert.isError && (
          <p className="text-sm text-red-600">
            Failed to create alert: {createAlert.error.message}
          </p>
        )}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={createAlert.isPending}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {createAlert.isPending ? 'Creating...' : 'Create Alert'}
          </button>
          <button
            type="button"
            onClick={() => navigate({ to: '/alerts' })}
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
