import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useAdminOrgs, useCreateOrg, useDeleteOrg, useUpdateOrg } from '../../../hooks/useAdmin'
import { useIsMobile } from '../../../hooks/useMediaQuery'

export const Route = createFileRoute('/_authenticated/admin/organisations')({
  component: AdminOrganisations,
})

function AdminOrganisations() {
  const isMobile = useIsMobile()
  const { data: orgs, isLoading } = useAdminOrgs()
  const createOrg = useCreateOrg()
  const updateOrg = useUpdateOrg()
  const deleteOrg = useDeleteOrg()

  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [openCardMenu, setOpenCardMenu] = useState<string | null>(null)

  const handleCreate = () => {
    if (!newName.trim()) return
    createOrg.mutate({ name: newName.trim() }, {
      onSuccess: () => { setNewName(''); setShowCreate(false) },
    })
  }

  const handleUpdate = (id: string) => {
    if (!editName.trim()) return
    updateOrg.mutate({ id, body: { name: editName.trim() } }, {
      onSuccess: () => setEditId(null),
    })
  }

  const handleDelete = (id: string, name: string) => {
    if (!confirm(`Delete organisation "${name}"? This cannot be undone.`)) return
    deleteOrg.mutate(id)
  }

  if (isLoading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/admin" className="text-sm text-blue-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">&larr; Admin</Link>
          <h1 className="text-2xl font-semibold text-gray-900 mt-1">Organisations</h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 min-h-[44px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          {isMobile ? 'Create' : 'Create Organisation'}
        </button>
      </div>

      {showCreate && (
        <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-2">New Organisation</h3>
          <div className={isMobile ? 'space-y-2' : 'flex gap-2'}>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Organisation name"
              className={`px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px] ${isMobile ? 'w-full' : 'flex-1'}`}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            />
            <div className={isMobile ? 'flex gap-2' : 'contents'}>
              <button onClick={handleCreate} className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 min-h-[44px] flex-1 md:flex-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
                Save
              </button>
              <button onClick={() => { setShowCreate(false); setNewName('') }} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 min-h-[44px] flex-1 md:flex-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
                Cancel
              </button>
            </div>
          </div>
          {createOrg.isError && <p className="text-red-600 text-sm mt-2">{(createOrg.error as Error).message}</p>}
        </div>
      )}

      {/* Organisations list - responsive */}
      {isMobile ? (
        // Mobile card view
        <div className="space-y-3">
          {orgs?.map((org) => (
            <div key={org.id} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{org.name}</h3>
                  <p className="text-sm text-gray-600">
                    Created {new Date(org.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => setOpenCardMenu(openCardMenu === org.id ? null : org.id)}
                  className="p-2 text-gray-500 hover:text-gray-700 min-h-[44px] min-w-[44px] flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  aria-label="Actions"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
              </div>

              {/* Action menu */}
              {openCardMenu === org.id && (
                <div className="pt-3 border-t border-gray-200 space-y-2">
                  <button
                    onClick={() => {
                      setEditId(org.id)
                      setEditName(org.name)
                      setOpenCardMenu(null)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 rounded min-h-[44px] flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  >
                    Edit Name
                  </button>
                  <button
                    onClick={() => {
                      handleDelete(org.id, org.name)
                      setOpenCardMenu(null)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded min-h-[44px] flex items-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  >
                    Delete Organisation
                  </button>
                </div>
              )}
            </div>
          ))}
          {!orgs?.length && (
            <div className="bg-white p-8 rounded-lg border border-gray-200 text-center text-gray-500">
              No organisations yet.
            </div>
          )}
        </div>
      ) : (
        // Desktop table view
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Created</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {orgs?.map((org) => (
                <tr key={org.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-3">
                    {editId === org.id ? (
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="px-2 py-1 border border-gray-300 rounded text-sm"
                          onKeyDown={(e) => e.key === 'Enter' && handleUpdate(org.id)}
                        />
                        <button onClick={() => handleUpdate(org.id)} className="text-green-600 hover:text-green-800 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">Save</button>
                        <button onClick={() => setEditId(null)} className="text-gray-500 hover:text-gray-700 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">Cancel</button>
                      </div>
                    ) : (
                      <span className="font-medium text-gray-900">{org.name}</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{new Date(org.created_at).toLocaleDateString()}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => { setEditId(org.id); setEditName(org.name) }}
                      className="text-blue-600 hover:text-blue-800 text-sm mr-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(org.id, org.name)}
                      className="text-red-600 hover:text-red-800 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {!orgs?.length && (
                <tr><td colSpan={3} className="px-4 py-8 text-center text-gray-500">No organisations yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
