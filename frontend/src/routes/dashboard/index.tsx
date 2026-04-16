import { createFileRoute } from '@tanstack/react-router'
import { useDevices } from '../../hooks/useDevices'
import { DeviceCard } from '../../components/DeviceCard'

export const Route = createFileRoute('/dashboard/')({
  component: DashboardIndex,
})

function DashboardIndex() {
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
