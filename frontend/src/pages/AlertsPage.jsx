import { useState, useEffect } from 'react'
import api from '../api/client'
import { Bell, BellOff, CheckCheck } from 'lucide-react'

const alertConfig = {
  low_stock: { color: 'bg-red-50 border-red-200 text-red-800', badge: 'badge-red', label: 'Low Stock' },
  dead_stock: { color: 'bg-orange-50 border-orange-200 text-orange-800', badge: 'badge-yellow', label: 'Dead Stock' },
  slow_mover: { color: 'bg-yellow-50 border-yellow-200 text-yellow-800', badge: 'badge-yellow', label: 'Slow Mover' },
  cash_warning: { color: 'bg-red-50 border-red-200 text-red-800', badge: 'badge-red', label: 'Cash Warning' },
  demand: { color: 'bg-blue-50 border-blue-200 text-blue-800', badge: 'badge-blue', label: 'Demand Signal' },
  daily_insight: { color: 'bg-indigo-50 border-indigo-200 text-indigo-800', badge: 'badge-blue', label: 'Daily Insight' },
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    api.get('/alerts/').then(res => setAlerts(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const markRead = async (id) => {
    await api.put(`/alerts/${id}/read`)
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a))
  }

  const markAllRead = async () => {
    await api.put('/alerts/read-all')
    setAlerts(prev => prev.map(a => ({ ...a, is_read: true })))
  }

  const unread = alerts.filter(a => !a.is_read).length

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          {unread > 0 && <p className="text-sm text-gray-500 mt-1">{unread} unread alert{unread > 1 ? 's' : ''}</p>}
        </div>
        {unread > 0 && (
          <button onClick={markAllRead} className="flex items-center gap-2 btn-secondary text-sm">
            <CheckCheck size={16} /> Mark all read
          </button>
        )}
      </div>

      {loading ? <p className="text-gray-400">Loading...</p> : (
        alerts.length === 0 ? (
          <div className="card text-center py-16 text-gray-400">
            <BellOff size={48} className="mx-auto mb-4 text-gray-200" />
            <p className="font-medium">No alerts yet</p>
            <p className="text-sm mt-1">Run an AI check to generate alerts based on your business data</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map(alert => {
              const config = alertConfig[alert.type] || alertConfig.daily_insight
              return (
                <div key={alert.id}
                  className={`border rounded-xl p-4 flex items-start gap-4 transition-opacity ${config.color} ${alert.is_read ? 'opacity-60' : ''}`}>
                  <Bell size={18} className="flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full bg-white/50`}>
                        {config.label}
                      </span>
                      {!alert.is_read && (
                        <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-sm">{alert.message}</p>
                    <p className="text-xs opacity-60 mt-1">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {!alert.is_read && (
                    <button onClick={() => markRead(alert.id)}
                      className="text-xs underline opacity-70 hover:opacity-100 flex-shrink-0">
                      Mark read
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )
      )}
    </div>
  )
}
