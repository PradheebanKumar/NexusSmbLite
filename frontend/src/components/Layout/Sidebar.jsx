import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  LayoutDashboard, MessageSquare, Package, TrendingUp,
  CheckSquare, Bell, BarChart2, LogOut, Share2, Zap
} from 'lucide-react'

const navSections = [
  {
    label: 'Overview',
    items: [
      { to: '/',             label: 'Dashboard',    icon: LayoutDashboard, end: true },
      { to: '/chat',         label: 'AI Assistant', icon: MessageSquare },
    ]
  },
  {
    label: 'Business',
    items: [
      { to: '/inventory',   label: 'Inventory',    icon: Package },
      { to: '/sales',       label: 'Sales',        icon: TrendingUp },
      { to: '/analytics',   label: 'Analytics',    icon: BarChart2 },
    ]
  },
  {
    label: 'Customers',
    items: [
      { to: '/customer-bot', label: 'Customer Bot', icon: Share2, badge: 'Live', badgeColor: 'bg-emerald-500' },
    ]
  },
  {
    label: 'Actions',
    items: [
      { to: '/approvals',   label: 'Approvals',    icon: CheckSquare },
      { to: '/alerts',      label: 'Alerts',       icon: Bell },
    ]
  },
]

export default function Sidebar() {
  const { owner, logout } = useAuth()
  const initials = owner?.shop_name?.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() || 'NS'

  return (
    <aside
      className="w-[220px] flex flex-col h-screen fixed left-0 top-0 z-30"
      style={{ background: 'linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%)' }}
    >
      {/* ── Brand ───────────────────────────────────────── */}
      <div className="px-4 pt-5 pb-4">
        <div className="flex items-center gap-2.5 mb-5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
            style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-white text-sm leading-tight">Nexus-SMB</p>
            <p className="text-indigo-400 text-[10px] tracking-wide">AI Workforce</p>
          </div>
        </div>

        {/* Shop card */}
        <div className="rounded-xl px-3 py-2.5" style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-[11px] font-bold shrink-0"
              style={{ background: 'linear-gradient(135deg, #f59e0b, #ef4444)' }}>
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-white text-[11px] font-semibold truncate">{owner?.shop_name}</p>
              <p className="text-indigo-300 text-[10px] truncate">{owner?.name}</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Nav ─────────────────────────────────────────── */}
      <nav className="flex-1 px-3 overflow-y-auto space-y-4 pb-3">
        {navSections.map(section => (
          <div key={section.label}>
            <p className="text-[10px] font-bold tracking-widest uppercase px-2 mb-1" style={{ color: 'rgba(165,180,252,0.5)' }}>
              {section.label}
            </p>
            <div className="space-y-0.5">
              {section.items.map(({ to, label, icon: Icon, end, badge, badgeColor }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `group flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium transition-all duration-150 ${
                      isActive
                        ? 'text-white shadow-lg'
                        : 'text-indigo-300 hover:text-white'
                    }`
                  }
                  style={({ isActive }) => isActive
                    ? { background: 'linear-gradient(135deg, #4f46e5, #6d28d9)', boxShadow: '0 4px 15px rgba(99,102,241,0.35)' }
                    : { background: 'transparent' }
                  }
                  onMouseEnter={e => { if (!e.currentTarget.classList.contains('text-white')) e.currentTarget.style.background = 'rgba(255,255,255,0.06)' }}
                  onMouseLeave={e => { if (!e.currentTarget.classList.contains('text-white')) e.currentTarget.style.background = 'transparent' }}
                >
                  {({ isActive }) => (
                    <>
                      <Icon size={15} className={`shrink-0 transition-colors ${isActive ? 'text-white' : 'text-indigo-400 group-hover:text-indigo-200'}`} />
                      <span className="flex-1 truncate">{label}</span>
                      {badge && (
                        <span className={`text-[9px] ${badgeColor || 'bg-indigo-500'} text-white px-1.5 py-0.5 rounded-full font-bold`}>
                          {badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* ── Logout ──────────────────────────────────────── */}
      <div className="px-3 pb-5 border-t" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
        <button
          onClick={logout}
          className="group flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium w-full transition-all duration-150 mt-3"
          style={{ color: 'rgba(165,180,252,0.7)' }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(239,68,68,0.1)'; e.currentTarget.style.color = '#fca5a5' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'rgba(165,180,252,0.7)' }}
        >
          <LogOut size={15} className="shrink-0" />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
