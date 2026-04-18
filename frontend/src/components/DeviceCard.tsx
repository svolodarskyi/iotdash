import { Link } from '@tanstack/react-router'
import type { Device } from '../types/api'

export function DeviceCard({ device }: { device: Device }) {
  return (
    <Link
      to="/dashboard/$deviceId"
      params={{ deviceId: device.id }}
      className="block bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium text-gray-900">{device.name}</h3>
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            device.is_active
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-600'
          }`}
        >
          {device.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>
      <p className="text-sm text-gray-500">Code: {device.device_code}</p>
      <p className="text-sm text-gray-500">Type: {device.device_type_name}</p>
    </Link>
  )
}
