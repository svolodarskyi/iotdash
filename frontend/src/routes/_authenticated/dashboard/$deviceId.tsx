import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { useDevice } from '../../../hooks/useDevice'
import { useDeviceEmbedUrls } from '../../../hooks/useDeviceEmbedUrls'
import { GrafanaEmbed } from '../../../components/GrafanaEmbed'
import { apiFetch } from '../../../lib/api'
import type { DeviceMetric } from '../../../types/api'

export const Route = createFileRoute('/_authenticated/dashboard/$deviceId')({
  component: DeviceDetail,
})

function DeviceDetail() {
  const { deviceId } = Route.useParams()
  const { data: device, isLoading: deviceLoading } = useDevice(deviceId)
  const { data: embedData, isLoading: embedLoading, error: embedError } = useDeviceEmbedUrls(deviceId)
  const { data: deviceMetrics } = useQuery({
    queryKey: ['devices', deviceId, 'metrics'],
    queryFn: () => apiFetch<DeviceMetric[]>(`/api/devices/${deviceId}/metrics`),
  })
  const [refreshKey, setRefreshKey] = useState(0)
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string> | null>(null)

  if (deviceLoading || embedLoading) {
    return <p className="text-gray-500">Loading...</p>
  }

  if (!device) {
    return <p className="text-red-600">Device not found.</p>
  }

  // Check if embed URLs failed due to permissions (403)
  const isAdminOnly = embedError && embedError instanceof Error &&
    embedError.message.includes('403')

  // Determine which metrics are selected (default: all)
  const enabledMetrics = deviceMetrics?.filter((m) => m.is_enabled) ?? []
  const activeSelection = selectedMetrics ?? new Set(enabledMetrics.map((m) => m.metric_name))

  const toggleMetric = (name: string) => {
    const next = new Set(activeSelection)
    if (next.has(name)) {
      next.delete(name)
    } else {
      next.add(name)
    }
    setSelectedMetrics(next)
  }

  const selectAll = () => {
    setSelectedMetrics(null)
  }

  // Filter embed URLs by selected metrics
  const filteredUrls = embedData?.urls.filter((embed) => {
    // Match by metric name in embed title or URL
    for (const name of activeSelection) {
      if (embed.dashboard_title.toLowerCase().includes(name.toLowerCase())) return true
      if (embed.url.includes(`var-metric=${name}`)) return true
    }
    // If no metrics defined, show all
    return enabledMetrics.length === 0
  }) ?? []

  return (
    <div>
      <div className="mb-6">
        <Link to="/dashboard" className="text-sm text-blue-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
          &larr; Back to devices
        </Link>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">{device.name}</h2>
          <p className="text-sm text-gray-500">
            {device.device_code} &middot; {device.device_type_name}
          </p>
        </div>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          Refresh Panels
        </button>
      </div>

      {/* Metric selector */}
      {enabledMetrics.length > 0 && (
        <div className="mb-6 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
          <button
            onClick={selectAll}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${
              selectedMetrics === null
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Show All
          </button>
          {enabledMetrics.map((m) => (
            <button
              key={m.metric_id}
              onClick={() => toggleMetric(m.metric_name)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors whitespace-nowrap min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${
                activeSelection.has(m.metric_name)
                  ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-300'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              {m.metric_name} {m.metric_unit && `(${m.metric_unit})`}
            </button>
          ))}
        </div>
      )}

      {isAdminOnly ? (
        <div className="p-6 bg-amber-50 border border-amber-200 rounded-lg">
          <h3 className="text-lg font-medium text-amber-900 mb-2">Admin Access Required</h3>
          <p className="text-sm text-amber-700">
            Grafana visualizations are only available to administrators.
            Please contact your system administrator if you need access to device metrics.
          </p>
        </div>
      ) : filteredUrls.length ? (
        <div className="grid grid-cols-1 gap-6">
          {filteredUrls.map((embed, idx) => (
            <GrafanaEmbed
              key={`${embed.url}-${refreshKey}-${idx}`}
              url={embed.url}
              title={embed.dashboard_title}
              refreshKey={refreshKey}
            />
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No panels configured for this device.</p>
      )}
    </div>
  )
}
