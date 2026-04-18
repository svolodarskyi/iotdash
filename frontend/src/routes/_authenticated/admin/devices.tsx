import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import {
  useAdminDevices,
  useAdminOrgs,
  useCreateDevice,
  useDeleteDevice,
  useDeviceTypes,
  useMetrics,
  useSyncDeviceConfig,
  useUpdateDevice,
  useUpdateDeviceMetrics,
} from '../../../hooks/useAdmin'
import type { DeviceAdmin } from '../../../types/api'

export const Route = createFileRoute('/_authenticated/admin/devices')({
  component: AdminDevices,
})

function AdminDevices() {
  const [orgFilter, setOrgFilter] = useState<string>('')
  const [deviceTypeFilter, setDeviceTypeFilter] = useState<string>('')
  const [metricFilter, setMetricFilter] = useState<string>('')
  const { data: orgs } = useAdminOrgs()
  const { data: devices, isLoading } = useAdminDevices(
    orgFilter || undefined,
    deviceTypeFilter || undefined,
    metricFilter || undefined,
  )
  const { data: metrics } = useMetrics()
  const { data: deviceTypes } = useDeviceTypes()
  const createDevice = useCreateDevice()
  const updateDevice = useUpdateDevice()
  const deleteDevice = useDeleteDevice()
  const updateMetrics = useUpdateDeviceMetrics()
  const syncConfig = useSyncDeviceConfig()

  const [showCreate, setShowCreate] = useState(false)
  const [autoCode, setAutoCode] = useState(true)
  const [form, setForm] = useState({
    device_code: '',
    name: '',
    organisation_id: '',
    device_type_id: '',
    metric_ids: [] as string[],
    auto_enable: false,
  })

  const [metricsModal, setMetricsModal] = useState<DeviceAdmin | null>(null)
  const [modalMetricIds, setModalMetricIds] = useState<string[]>([])
  const [modalSendConfig, setModalSendConfig] = useState(false)

  // Inline edit state
  const [editDeviceId, setEditDeviceId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ name: '', device_type_id: '', is_active: true })

  // Get allowed metrics for selected device type in create form
  const selectedDeviceType = deviceTypes?.find((dt) => dt.id === form.device_type_id)
  const allowedMetricIds = new Set(selectedDeviceType?.allowed_metrics.map((m) => m.metric_id) ?? [])

  const handleCreate = () => {
    if (!form.name || !form.organisation_id || !form.device_type_id) return
    createDevice.mutate(
      {
        ...form,
        device_code: autoCode ? undefined : form.device_code || undefined,
      },
      {
        onSuccess: () => {
          setForm({ device_code: '', name: '', organisation_id: '', device_type_id: '', metric_ids: [], auto_enable: false })
          setShowCreate(false)
          setAutoCode(true)
        },
      },
    )
  }

  const toggleMetric = (metricId: string, list: string[], setter: (v: string[]) => void) => {
    setter(list.includes(metricId) ? list.filter((id) => id !== metricId) : [...list, metricId])
  }

  const handleDelete = (id: string, name: string) => {
    if (!confirm(`Delete device "${name}"? All alerts and metric links will be removed.`)) return
    deleteDevice.mutate(id)
  }

  const openMetricsModal = (device: DeviceAdmin) => {
    setMetricsModal(device)
    setModalMetricIds(device.metrics.filter((m) => m.is_enabled).map((m) => m.metric_id))
    setModalSendConfig(false)
  }

  const handleUpdateMetrics = () => {
    if (!metricsModal) return
    updateMetrics.mutate(
      { id: metricsModal.id, body: { metric_ids: modalMetricIds, send_config: modalSendConfig } },
      { onSuccess: () => setMetricsModal(null) },
    )
  }

  // Get allowed metrics for device in metrics modal
  const modalDeviceType = deviceTypes?.find((dt) => dt.id === metricsModal?.device_type_id)
  const modalAllowedMetricIds = new Set(modalDeviceType?.allowed_metrics.map((m) => m.metric_id) ?? [])

  const startEdit = (device: DeviceAdmin) => {
    setEditDeviceId(device.id)
    setEditForm({
      name: device.name,
      device_type_id: device.device_type_id,
      is_active: device.is_active,
    })
  }

  const handleSaveEdit = () => {
    if (!editDeviceId) return
    updateDevice.mutate(
      { id: editDeviceId, body: editForm },
      { onSuccess: () => setEditDeviceId(null) },
    )
  }

  // When device type changes in create form, clear metrics that are no longer allowed
  const handleDeviceTypeChange = (newTypeId: string) => {
    const newType = deviceTypes?.find((dt) => dt.id === newTypeId)
    const newAllowed = new Set(newType?.allowed_metrics.map((m) => m.metric_id) ?? [])
    setForm({
      ...form,
      device_type_id: newTypeId,
      metric_ids: form.metric_ids.filter((id) => newAllowed.has(id)),
    })
  }

  if (isLoading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/admin" className="text-sm text-blue-600 hover:underline">&larr; Admin</Link>
          <h1 className="text-2xl font-semibold text-gray-900 mt-1">Devices</h1>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
          Provision Device
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Provision New Device</h3>
          <div className="grid grid-cols-2 gap-3">
            <input type="text" placeholder="Device name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="px-3 py-2 border border-gray-300 rounded-md text-sm" />
            <select value={form.organisation_id} onChange={(e) => setForm({ ...form, organisation_id: e.target.value })} className="px-3 py-2 border border-gray-300 rounded-md text-sm">
              <option value="">Select organisation</option>
              {orgs?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
            <div className="col-span-2">
              <label className="flex items-center gap-2 text-sm text-gray-700 mb-2">
                <input type="checkbox" checked={autoCode} onChange={(e) => setAutoCode(e.target.checked)} />
                Auto-generate device UID
              </label>
              <input
                type="text"
                placeholder={autoCode ? 'Auto-generated on save' : 'Device UID (e.g. sensor04)'}
                value={autoCode ? '' : form.device_code}
                onChange={(e) => setForm({ ...form, device_code: e.target.value })}
                disabled={autoCode}
                className={`px-3 py-2 border border-gray-300 rounded-md text-sm w-full ${autoCode ? 'bg-gray-100 text-gray-400' : ''}`}
              />
            </div>
            <select
              value={form.device_type_id}
              onChange={(e) => handleDeviceTypeChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="">Select device type</option>
              {deviceTypes?.map((dt) => <option key={dt.id} value={dt.id}>{dt.name}</option>)}
            </select>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Metrics</p>
            {!form.device_type_id && (
              <p className="text-xs text-gray-400">Select a device type to see available metrics</p>
            )}
            <div className="flex flex-wrap gap-2">
              {metrics?.filter((m) => allowedMetricIds.has(m.id)).map((m) => (
                <label key={m.id} className="flex items-center gap-1.5 text-sm text-gray-700">
                  <input type="checkbox" checked={form.metric_ids.includes(m.id)} onChange={() => toggleMetric(m.id, form.metric_ids, (v) => setForm({ ...form, metric_ids: v }))} />
                  {m.name} {m.unit && `(${m.unit})`}
                </label>
              ))}
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input type="checkbox" checked={form.auto_enable} onChange={(e) => setForm({ ...form, auto_enable: e.target.checked })} />
            Send config to device immediately (auto-enable)
          </label>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700">Provision</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
          </div>
          {createDevice.isError && <p className="text-red-600 text-sm">{(createDevice.error as Error).message}</p>}
        </div>
      )}

      {/* Filters — below create form */}
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

      {/* Devices table */}
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
              <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {devices?.map((d) => (
              <tr key={d.id} className="border-b border-gray-100 last:border-0">
                {editDeviceId === d.id ? (
                  <>
                    <td className="px-4 py-3 font-mono text-gray-900">{d.device_code}</td>
                    <td className="px-4 py-3">
                      <input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="px-2 py-1 border border-gray-300 rounded text-sm w-full" />
                    </td>
                    <td className="px-4 py-3 text-gray-500">{d.organisation_name}</td>
                    <td className="px-4 py-3">
                      <select value={editForm.device_type_id} onChange={(e) => setEditForm({ ...editForm, device_type_id: e.target.value })} className="px-2 py-1 border border-gray-300 rounded text-sm">
                        {deviceTypes?.map((dt) => <option key={dt.id} value={dt.id}>{dt.name}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {d.metrics.filter((m) => m.is_enabled).map((m) => (
                          <span key={m.metric_id} className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                            {m.metric_name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={editForm.is_active} onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })} />
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button onClick={handleSaveEdit} className="text-green-600 hover:text-green-800 text-sm">Save</button>
                      <button onClick={() => setEditDeviceId(null)} className="text-gray-500 hover:text-gray-700 text-sm">Cancel</button>
                    </td>
                  </>
                ) : (
                  <>
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
                    <td className="px-4 py-3 text-right space-x-2">
                      <button onClick={() => startEdit(d)} className="text-yellow-600 hover:text-yellow-800 text-sm">Edit</button>
                      <button onClick={() => openMetricsModal(d)} className="text-blue-600 hover:text-blue-800 text-sm">Metrics</button>
                      <button
                        onClick={() => syncConfig.mutate(d.id)}
                        disabled={syncConfig.isPending}
                        className="text-indigo-600 hover:text-indigo-800 text-sm disabled:opacity-50"
                      >
                        {syncConfig.isPending ? 'Syncing...' : 'Sync'}
                      </button>
                      <button onClick={() => handleDelete(d.id, d.name)} className="text-red-600 hover:text-red-800 text-sm">Delete</button>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {!devices?.length && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No devices found.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Metrics modal */}
      {metricsModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Manage Metrics &mdash; {metricsModal.device_code}
            </h3>
            <p className="text-xs text-gray-500 mb-2">
              Only metrics allowed by device type "{metricsModal.device_type_name}" are shown.
            </p>
            <div className="space-y-2 mb-4">
              {metrics?.filter((m) => modalAllowedMetricIds.has(m.id)).map((m) => (
                <label key={m.id} className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={modalMetricIds.includes(m.id)} onChange={() => toggleMetric(m.id, modalMetricIds, setModalMetricIds)} />
                  {m.name} {m.unit && `(${m.unit})`}
                </label>
              ))}
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-700 mb-4">
              <input type="checkbox" checked={modalSendConfig} onChange={(e) => setModalSendConfig(e.target.checked)} />
              Send config to device after update
            </label>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setMetricsModal(null)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button onClick={handleUpdateMetrics} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
