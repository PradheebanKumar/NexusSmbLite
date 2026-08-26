import { useState, useEffect } from 'react'
import api from '../api/client'
import { CheckCircle, XCircle, Edit2, Clock, History } from 'lucide-react'

function ActionCard({ action, onResolved }) {
  const [editing, setEditing] = useState(false)
  const [content, setContent] = useState(action.generated_content || '')
  const [loading, setLoading] = useState(false)

  const resolve = async (status) => {
    setLoading(true)
    try {
      await api.put(`/actions/${action.id}`, {
        status,
        edited_content: editing ? content : undefined
      })
      onResolved()
    } catch (e) {
      alert('Error: ' + (e.response?.data?.detail || e.message))
    } finally {
      setLoading(false)
    }
  }

  const typeColors = {
    send_whatsapp_offer: 'bg-green-50 border-green-200',
    reorder_reminder: 'bg-blue-50 border-blue-200',
    update_price: 'bg-amber-50 border-amber-200',
    notify_demand_customers: 'bg-purple-50 border-purple-200',
  }

  const typeBadge = {
    send_whatsapp_offer: 'Offer Message',
    reorder_reminder: 'Reorder Alert',
    update_price: 'Price Update',
    notify_demand_customers: 'Customer Notification',
  }

  return (
    <div className={`rounded-xl border p-5 ${typeColors[action.action_type] || 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            {typeBadge[action.action_type] || action.action_type}
          </span>
          <h3 className="font-semibold text-gray-900 mt-0.5">{action.title}</h3>
        </div>
        <span className="text-xs text-gray-400 flex-shrink-0">
          {new Date(action.created_at).toLocaleString()}
        </span>
      </div>

      <p className="text-sm text-gray-600 mb-4">{action.description}</p>

      {action.generated_content && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs font-medium text-gray-500">Generated Content</label>
            <button onClick={() => setEditing(!editing)}
              className="text-xs text-blue-600 flex items-center gap-1 hover:underline">
              <Edit2 size={12} /> {editing ? 'Done editing' : 'Edit'}
            </button>
          </div>
          {editing ? (
            <textarea
              className="input text-sm"
              rows={4}
              value={content}
              onChange={e => setContent(e.target.value)}
            />
          ) : (
            <div className="bg-white/70 rounded-lg px-4 py-3 text-sm text-gray-700 border border-white/50 whitespace-pre-wrap">
              {content}
            </div>
          )}
        </div>
      )}

      <div className="flex gap-3">
        <button onClick={() => resolve('approved')} disabled={loading}
          className="flex items-center gap-2 btn-success flex-1 justify-center">
          <CheckCircle size={16} /> Approve
        </button>
        <button onClick={() => resolve('rejected')} disabled={loading}
          className="flex items-center gap-2 btn-danger flex-1 justify-center">
          <XCircle size={16} /> Reject
        </button>
      </div>
    </div>
  )
}

export default function ApprovalsPage() {
  const [actions, setActions] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('pending')

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/actions/'),
      api.get('/actions/history')
    ]).then(([a, h]) => {
      setActions(a.data)
      setHistory(h.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Approval Panel</h1>

      <div className="flex gap-2 mb-6">
        {[
          { key: 'pending', label: `Pending (${actions.length})`, icon: Clock },
          { key: 'history', label: 'History', icon: History }
        ].map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === key ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}>
            <Icon size={16} /> {label}
          </button>
        ))}
      </div>

      {loading ? <p className="text-gray-400">Loading...</p> : (
        activeTab === 'pending' ? (
          actions.length === 0 ? (
            <div className="card text-center py-16 text-gray-400">
              <CheckCircle size={48} className="mx-auto mb-4 text-gray-200" />
              <p className="font-medium">No pending actions</p>
              <p className="text-sm mt-1">Run an AI check from the dashboard to generate suggestions</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {actions.map(action => (
                <ActionCard key={action.id} action={action} onResolved={load} />
              ))}
            </div>
          )
        ) : (
          <div className="card overflow-hidden p-0">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {['Action', 'Type', 'Status', 'Created', 'Resolved'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {history.map(a => (
                  <tr key={a.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{a.title}</td>
                    <td className="px-4 py-3 text-gray-500">{a.action_type}</td>
                    <td className="px-4 py-3">
                      <span className={a.status === 'approved' || a.status === 'executed' ? 'badge-green' :
                        a.status === 'rejected' ? 'badge-red' : 'badge-yellow'}>
                        {a.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{new Date(a.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-gray-500">{a.resolved_at ? new Date(a.resolved_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">No history yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  )
}
