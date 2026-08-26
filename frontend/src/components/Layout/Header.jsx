import { useLocation, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Bell } from 'lucide-react'
import { useState, useEffect } from 'react'
import api from '../../api/client'

const PAGE_TITLES = {
  '/':             { title: 'Dashboard',    sub: 'Your business at a glance' },
  '/chat':         { title: 'AI Assistant', sub: 'Talk to your AI business co-pilot' },
  '/inventory':    { title: 'Inventory',    sub: 'Manage products and stock levels' },
  '/sales':        { title: 'Sales',        sub: 'Record and review transactions' },
  '/analytics':    { title: 'Analytics & Growth', sub: 'P&L, health score, revenue advisor' },
  '/approvals':    { title: 'Approvals',    sub: 'Review AI-suggested actions' },
  '/alerts':       { title: 'Alerts',       sub: 'Business notifications and warnings' },
  '/customer-bot': { title: 'Customer Bot', sub: 'Share your shop link with customers' },
}

export default function Header() {
  const { owner } = useAuth()
  const location  = useLocation()
  const [unread, setUnread] = useState(0)

  const page = PAGE_TITLES[location.pathname] || { title: 'Nexus-SMB', sub: '' }
  const initials = owner?.name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || '?'

  useEffect(() => {
    api.get('/alerts/').then(r => {
      setUnread((r.data || []).filter(a => !a.is_read).length)
    }).catch(() => {})
  }, [location.pathname])

  return (
    <header className="h-14 bg-white border-b border-gray-100 flex items-center px-6 gap-4 sticky top-0 z-20 shadow-sm">
      {/* Page title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-base font-bold text-gray-900 leading-tight truncate">{page.title}</h1>
        <p className="text-xs text-gray-400 leading-tight hidden sm:block">{page.sub}</p>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 shrink-0">
        {/* Alerts bell */}
        <Link to="/alerts" className="relative p-2 rounded-xl hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors">
          <Bell size={18} />
          {unread > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </Link>

        {/* Owner avatar */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-gray-100">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-white text-xs font-bold"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
            {initials}
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold text-gray-800 leading-tight">{owner?.name}</p>
            <p className="text-[10px] text-gray-400 leading-tight">{owner?.shop_name}</p>
          </div>
        </div>
      </div>
    </header>
  )
}
