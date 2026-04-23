import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect, useMemo } from 'react'
import { useDevices, useDeviceMetrics } from '../../../hooks/useDevices'
import { useAdminDevices, useAdminOrgs, useMetrics } from '../../../hooks/useAdmin'
import { useCreateAlert } from '../../../hooks/useAlerts'
import { useAuthStore } from '../../../store/authStore'
import { useIsMobile } from '../../../hooks/useMediaQuery'

export const Route = createFileRoute('/_authenticated/alerts/new')({
  component: NewAlert,
})

function NewAlert() {
  const isMobile = useIsMobile()
  const navigate = useNavigate()
  const createAlert = useCreateAlert()
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  // Admin filters
  const [filterOrgId, setFilterOrgId] = useState('')
  const [filterMetricName, setFilterMetricName] = useState('')
  const { data: orgs } = useAdminOrgs()
  const { data: allMetrics } = useMetrics()

  // Device lists
  const { data: viewerDevices, isLoading: viewerLoading } = useDevices()
  const { data: adminDevices, isLoading: adminLoading } = useAdminDevices(
    filterOrgId || undefined,
    undefined,
    filterMetricName || undefined,
  )

  const devices = isAdmin ? adminDevices : viewerDevices
  const devicesLoading = isAdmin ? adminLoading : viewerLoading

  // Form state
  const [deviceId, setDeviceId] = useState('')
  const [metric, setMetric] = useState('')
  const [condition, setCondition] = useState('above')
  const [threshold, setThreshold] = useState('30')
  const [durationSeconds, setDurationSeconds] = useState('60')
  const [email, setEmail] = useState(user?.email ?? '')

  const { data: deviceMetrics } = useDeviceMetrics(deviceId || undefined)

  // Reset device when filters change
  useEffect(() => {
    setDeviceId('')
  }, [filterOrgId, filterMetricName])

  // When device changes, reset metric to first available
  useEffect(() => {
    if (deviceMetrics?.length) {
      setMetric(deviceMetrics[0].metric_name)
    } else {
      setMetric('')
    }
  }, [deviceMetrics])

  // Group admin devices by org name for the dropdown
  const groupedDevices = useMemo(() => {
    if (!isAdmin || !adminDevices) return null
    return adminDevices.reduce<Record<string, typeof adminDevices>>((acc, d) => {
      const org = d.organisation_name
      if (!acc[org]) acc[org] = []
      acc[org].push(d)
      return acc
    }, {})
  }, [isAdmin, adminDevices])

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
        {isAdmin && (
          <div className={isMobile ? 'space-y-4' : 'grid grid-cols-2 gap-4'}>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company
              </label>
              <select
                value={filterOrgId}
                onChange={(e) => setFilterOrgId(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
              >
                <option value="">All companies</option>
                {orgs?.map((o) => (
                  <option key={o.id} value={o.id}>{o.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Metric Type
              </label>
              <select
                value={filterMetricName}
                onChange={(e) => setFilterMetricName(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
              >
                <option value="">All metrics</option>
                {allMetrics?.map((m) => (
                  <option key={m.id} value={m.name}>
                    {m.name}{m.unit ? ` (${m.unit})` : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

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
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
            >
              <option value="">Select a device</option>
              {isAdmin && groupedDevices
                ? Object.entries(groupedDevices).map(([orgName, orgDevices]) => (
                    <optgroup key={orgName} label={orgName}>
                      {orgDevices.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.device_code})
                        </option>
                      ))}
                    </optgroup>
                  ))
                : devices?.map((d) => (
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
          {!deviceId ? (
            <select disabled className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm bg-gray-50 text-gray-400 min-h-[44px]">
              <option>Select a device first</option>
            </select>
          ) : !deviceMetrics?.length ? (
            <select disabled className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm bg-gray-50 text-gray-400 min-h-[44px]">
              <option>No metrics configured</option>
            </select>
          ) : (
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
            >
              {deviceMetrics.map((dm) => (
                <option key={dm.metric_id} value={dm.metric_name}>
                  {dm.metric_name}{dm.metric_unit ? ` (${dm.metric_unit})` : ''}
                </option>
              ))}
            </select>
          )}
        </div>

        <div className={isMobile ? 'space-y-4' : 'grid grid-cols-2 gap-4'}>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Condition
            </label>
            <select
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
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
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
              inputMode="decimal"
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
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
            inputMode="numeric"
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
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm min-h-[44px]"
            inputMode="email"
          />
        </div>

        {createAlert.isError && (
          <p className="text-sm text-red-600">
            Failed to create alert: {createAlert.error.message}
          </p>
        )}

        <div className={isMobile ? 'space-y-2' : 'flex gap-3 pt-2'}>
          <button
            type="submit"
            disabled={createAlert.isPending || !metric}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 min-h-[44px] w-full md:w-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            {createAlert.isPending ? 'Creating...' : 'Create Alert'}
          </button>
          <button
            type="button"
            onClick={() => navigate({ to: '/alerts' })}
            className="border border-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-50 min-h-[44px] w-full md:w-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
