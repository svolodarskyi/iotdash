import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import {
  useAdminOrgs,
  useAdminUsers,
  useCreateUser,
  useDeleteUser,
  useUpdateUser,
} from '../../../hooks/useAdmin'
import { useIsMobile } from '../../../hooks/useMediaQuery'

export const Route = createFileRoute('/_authenticated/admin/users')({
  component: AdminUsers,
})

function AdminUsers() {
  const isMobile = useIsMobile()
  const [orgFilter, setOrgFilter] = useState<string>('')
  const { data: orgs } = useAdminOrgs()
  const { data: users, isLoading } = useAdminUsers(orgFilter || undefined)
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()
  const deleteUser = useDeleteUser()

  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ email: '', password: '', full_name: '', organisation_id: '' })
  const [editId, setEditId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ full_name: '', email: '' })
  const [openCardMenu, setOpenCardMenu] = useState<string | null>(null)

  const handleCreate = () => {
    if (!form.email || !form.password || !form.full_name || !form.organisation_id) return
    createUser.mutate(form, {
      onSuccess: () => {
        setForm({ email: '', password: '', full_name: '', organisation_id: '' })
        setShowCreate(false)
      },
    })
  }

  const handleUpdate = (id: string) => {
    updateUser.mutate({ id, body: editForm }, { onSuccess: () => setEditId(null) })
  }

  const handleDeactivate = (id: string, name: string) => {
    if (!confirm(`Deactivate user "${name}"?`)) return
    deleteUser.mutate(id)
  }

  if (isLoading) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link to="/admin" className="text-sm text-blue-600 hover:underline">&larr; Admin</Link>
          <h1 className="text-2xl font-semibold text-gray-900 mt-1">Users</h1>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 min-h-[44px]"
        >
          {isMobile ? 'Create' : 'Create User'}
        </button>
      </div>

      <div className="mb-4">
        <select
          value={orgFilter}
          onChange={(e) => setOrgFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm w-full md:w-auto min-h-[44px]"
        >
          <option value="">All organisations</option>
          {orgs?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
        </select>
      </div>

      {showCreate && (
        <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200 space-y-3">
          <h3 className="text-sm font-medium text-gray-700">New User</h3>
          <div className={isMobile ? 'space-y-3' : 'grid grid-cols-2 gap-3'}>
            <input
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px] w-full"
            />
            <input
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px] w-full"
            />
            <input
              type="text"
              placeholder="Full name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px] w-full"
            />
            <select
              value={form.organisation_id}
              onChange={(e) => setForm({ ...form, organisation_id: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm min-h-[44px] w-full"
            >
              <option value="">Select organisation</option>
              {orgs?.filter((o) => o.name !== 'Platform').map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 min-h-[44px] flex-1 md:flex-none"
            >
              Save
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 min-h-[44px] flex-1 md:flex-none"
            >
              Cancel
            </button>
          </div>
          {createUser.isError && <p className="text-red-600 text-sm">{(createUser.error as Error).message}</p>}
        </div>
      )}

      {/* Users list - responsive */}
      {isMobile ? (
        // Mobile card view
        <div className="space-y-3">
          {users?.map((u) => (
            <div key={u.id} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{u.full_name}</h3>
                  <p className="text-sm text-gray-600">{u.email}</p>
                </div>
                <button
                  onClick={() => setOpenCardMenu(openCardMenu === u.id ? null : u.id)}
                  className="p-2 text-gray-500 hover:text-gray-700 min-h-[44px] min-w-[44px] flex items-center justify-center"
                  aria-label="Actions"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                  </svg>
                </button>
              </div>

              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-1 rounded font-medium ${
                  u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {u.role}
                </span>
              </div>

              {/* Action menu */}
              {openCardMenu === u.id && (
                <div className="pt-3 border-t border-gray-200 space-y-2 mt-3">
                  <button
                    onClick={() => {
                      setEditId(u.id)
                      setEditForm({ full_name: u.full_name, email: u.email })
                      setOpenCardMenu(null)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 rounded min-h-[44px] flex items-center"
                  >
                    Edit User
                  </button>
                  <button
                    onClick={() => {
                      handleDeactivate(u.id, u.full_name)
                      setOpenCardMenu(null)
                    }}
                    className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded min-h-[44px] flex items-center"
                  >
                    Deactivate User
                  </button>
                </div>
              )}
            </div>
          ))}
          {!users?.length && (
            <div className="bg-white p-8 rounded-lg border border-gray-200 text-center text-gray-500">
              No users found.
            </div>
          )}
        </div>
      ) : (
        // Desktop table view
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Role</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Active</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users?.map((u) => (
                <tr key={u.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-3 text-gray-900">{editId === u.id ? (
                    <input value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} className="px-2 py-1 border border-gray-300 rounded text-sm w-full" />
                  ) : u.email}</td>
                  <td className="px-4 py-3 text-gray-700">{editId === u.id ? (
                    <input value={editForm.full_name} onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })} className="px-2 py-1 border border-gray-300 rounded text-sm w-full" />
                  ) : u.full_name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">-</td>
                  <td className="px-4 py-3 text-right">
                    {editId === u.id ? (
                      <>
                        <button onClick={() => handleUpdate(u.id)} className="text-green-600 hover:text-green-800 text-sm mr-2">Save</button>
                        <button onClick={() => setEditId(null)} className="text-gray-500 hover:text-gray-700 text-sm">Cancel</button>
                      </>
                    ) : (
                      <>
                        <button onClick={() => { setEditId(u.id); setEditForm({ full_name: u.full_name, email: u.email }) }} className="text-blue-600 hover:text-blue-800 text-sm mr-3">Edit</button>
                        <button onClick={() => handleDeactivate(u.id, u.full_name)} className="text-red-600 hover:text-red-800 text-sm">Deactivate</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {!users?.length && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No users found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
