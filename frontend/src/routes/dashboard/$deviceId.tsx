import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useDevice } from '../../hooks/useDevice'
import { useDeviceEmbedUrls } from '../../hooks/useDeviceEmbedUrls'
import { GrafanaEmbed } from '../../components/GrafanaEmbed'

export const Route = createFileRoute('/dashboard/$deviceId')({
  component: DeviceDetail,
})

function DeviceDetail() {
  const { deviceId } = Route.useParams()
  const { data: device, isLoading: deviceLoading } = useDevice(deviceId)
  const { data: embedData, isLoading: embedLoading } = useDeviceEmbedUrls(deviceId)
  const [refreshKey, setRefreshKey] = useState(0)

  if (deviceLoading || embedLoading) {
    return <p className="text-gray-500">Loading...</p>
  }

  if (!device) {
    return <p className="text-red-600">Device not found.</p>
  }

  return (
    <div>
      <div className="mb-6">
        <Link to="/dashboard" className="text-sm text-blue-600 hover:underline">
          &larr; Back to devices
        </Link>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">{device.name}</h2>
          <p className="text-sm text-gray-500">
            {device.device_code} &middot; {device.device_type}
          </p>
        </div>
        <button
          onClick={() => setRefreshKey((k) => k + 1)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Refresh Panels
        </button>
      </div>

      {embedData?.urls.length ? (
        <div className="grid grid-cols-1 gap-6">
          {embedData.urls.map((embed) => (
            <GrafanaEmbed
              key={`${embed.panel_id}-${refreshKey}`}
              url={embed.url}
              title={`${embed.dashboard_title} — Panel ${embed.panel_id}`}
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
