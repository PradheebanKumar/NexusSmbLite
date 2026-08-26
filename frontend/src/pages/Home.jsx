import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import {
  TrendingUp, TrendingDown, Package, Bell, CheckSquare,
  Zap, AlertTriangle, CheckCircle, Loader, X,
  BarChart2, MessageSquare, Share2, ArrowUpRight,
  ShoppingCart, DollarSign, Activity
} from 'lucide-react'

function StatCard({ label, value, sub, icon: Icon, gradient }) {
  const gradients = {
    blue:   'from-blue-500 to-indigo-600',
    green:  'from-emerald-500 to-teal-600',
    purple: 'from-purple-500 to-violet-600',
    amber:  'from-amber-500 to-orange-500',
    red:    'from-red-500 to-rose-600',
  }
  const g = gradients[gradient] || gradients.blue
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex flex-col gap-3 relative overflow-hidden">
      <div className={`absolute -top-6 -right-6 w-24 h-24 rounded-full bg-gradient-to-br ${g} opacity-[0.06]`} />
      <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${g} flex items-center justify-center shadow-sm shrink-0`}>
        <Icon size={18} className="text-white" />
      </div>
      <div>
        <p className="text-2xl font-black text-gray-900">{value}</p>
        <p className="text-sm text-gray-500 mt-0.5">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
      </div>
    </div>
  )
}

function AgentResultBanner({ result, onClose }) {
  if (!result) return null
  return (
    <div className="rounded-2xl border-2 border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50 p-5 relative">
      <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-white/60">
        <X size={15} />
      </button>
      <div className="flex items-center gap-2 mb-3">
        <div className="w-7 h-7 bg-emerald-500 rounded-full flex items-center justify-center">
          <CheckCircle size={14} className="text-white" />
        </div>
        <p className="font-bold text-emerald-900">AI Check Complete!</p>
      </div>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-white rounded-xl p-3 text-center shadow-sm">
          <p className="text-2xl font-black text-indigo-600">{result.alerts_created ?? 0}</p>
          <p className="text-xs text-gray-500 mt-0.5">Alerts generated</p>
        </div>
        <div className="bg-white rounded-xl p-3 text-center shadow-sm">
          <p className="text-2xl font-black text-purple-600">{result.actions_created ?? 0}</p>
          <p className="text-xs text-gray-500 mt-0.5">Actions queued</p>
        </div>
      </div>
      {result.insights?.[0] && (
        <div className="bg-white/70 rounded-xl p-3 mb-3">
          <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wide mb-1">AI Insight</p>
          <p className="text-sm text-gray-700 leading-relaxed">{result.insights[0]}</p>
        </div>
      )}
      <div className="flex gap-2">
        <Link to="/alerts" className="flex-1 text-center text-xs bg-indigo-600 text-white rounded-xl py-2 font-semibold hover:bg-indigo-700 transition-colors">View Alerts</Link>
        <Link to="/approvals" className="flex-1 text-center text-xs bg-purple-600 text-white rounded-xl py-2 font-semibold hover:bg-purple-700 transition-colors">Review Actions</Link>
      </div>
    </div>
  )
}

function QuickAction({ to, label, desc, gradient, icon: Icon }) {
  return (
    <Link to={to} className={`bg-gradient-to-br ${gradient} rounded-2xl p-4 text-white hover:opacity-90 transition-all duration-150 hover:shadow-lg hover:-translate-y-0.5 flex flex-col gap-3`}>
      <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
        <Icon size={18} />
      </div>
      <div>
        <p className="font-bold text-sm">{label}</p>
        <p className="text-xs opacity-75 mt-0.5">{desc}</p>
      </div>
      <div className="flex justify-end"><ArrowUpRight size={16} className="opacity-60" /></div>
    </Link>
  )
}

const ALERT_STYLE = {
  low_stock:     { bg: 'bg-red-50',    border: 'border-red-200',    dot: 'bg-red-400',    text: 'text-red-800'    },
  dead_stock:    { bg: 'bg-orange-50', border: 'border-orange-200', dot: 'bg-orange-400', text: 'text-orange-800' },
  cash_warning:  { bg: 'bg-amber-50',  border: 'border-amber-200',  dot: 'bg-amber-400',  text: 'text-amber-800'  },
  daily_insight: { bg: 'bg-blue-50',   border: 'border-blue-200',   dot: 'bg-blue-400',   text: 'text-blue-800'   },
}

export default function Home() {
  const { owner } = useAuth()
  const [summary, setSummary]           = useState(null)
  const [alerts, setAlerts]             = useState([])
  const [loading, setLoading]           = useState(true)
  const [agentRunning, setAgentRunning] = useState(false)
  const [agentResult, setAgentResult]   = useState(null)
  const [agentError, setAgentError]     = useState('')

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get('/analytics/dashboard-summary'),
      api.get('/alerts/')
    ]).then(([s, a]) => {
      setSummary(s.data)
      setAlerts((a.data || []).filter(al => !al.is_read).slice(0, 4))
    }).catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const runAgentCheck = async () => {
    setAgentRunning(true); setAgentResult(null); setAgentError('')
    try {
      const res = await api.post('/agents/run-check')
      setAgentResult(res.data.result || res.data)
      load()
    } catch (e) {
      setAgentError(e.response?.data?.detail || e.message || 'Unknown error')
    } finally { setAgentRunning(false) }
  }

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  if (loading) return (
    <div className="flex items-center justify-center h-64 gap-3 text-gray-400">
      <Loader size={20} className="animate-spin" />
      <span className="text-sm">Loading dashboard...</span>
    </div>
  )

  const today = summary?.today || {}
  const month = summary?.this_month || {}
  const inv   = summary?.inventory || {}

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-5">

      {/* ── Hero banner ── */}
      <div className="rounded-2xl p-6 flex items-center justify-between gap-4 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #312e81 100%)' }}>
        <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full opacity-10" style={{ background: 'radial-gradient(circle, #818cf8, transparent)' }} />
        <div className="absolute bottom-0 left-40 w-32 h-32 rounded-full opacity-[0.07]" style={{ background: '#a5b4fc' }} />
        <div className="relative z-10">
          <p className="text-indigo-300 text-sm font-medium mb-0.5">{greeting} 👋</p>
          <h1 className="text-2xl font-black text-white">{owner?.name}</h1>
          <p className="text-indigo-300 text-sm mt-1">
            {owner?.shop_name} &nbsp;·&nbsp; {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>
        </div>
        <button
          onClick={runAgentCheck}
          disabled={agentRunning}
          className="relative z-10 flex items-center gap-2 font-bold px-5 py-3 rounded-xl transition-all duration-150 shrink-0 disabled:opacity-60 text-sm"
          style={{ background: 'linear-gradient(135deg, #fbbf24, #f59e0b)', color: '#1c1917', boxShadow: '0 4px 20px rgba(251,191,36,0.3)' }}
        >
          {agentRunning ? <><Loader size={16} className="animate-spin" /> Analysing...</> : <><Zap size={16} /> Run AI Check</>}
        </button>
      </div>

      {agentResult && <AgentResultBanner result={agentResult} onClose={() => setAgentResult(null)} />}
      {agentError && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-2xl px-4 py-3 text-sm text-red-800">
          <AlertTriangle size={15} className="shrink-0 mt-0.5 text-red-500" />
          <span className="flex-1">{agentError}</span>
          <button onClick={() => setAgentError('')}><X size={13} className="text-red-400" /></button>
        </div>
      )}

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Today's Revenue"    value={`₹${(today.revenue || 0).toLocaleString('en-IN')}`}     sub={`${today.transactions || 0} transactions`} icon={ShoppingCart}   gradient="blue"   />
        <StatCard label="Today's Profit"     value={`₹${(today.profit || 0).toLocaleString('en-IN')}`}      sub="After stock cost"                           icon={today.profit >= 0 ? TrendingUp : TrendingDown} gradient={today.profit >= 0 ? 'green' : 'red'} />
        <StatCard label="Month Net Profit"   value={`₹${(month.net_profit || 0).toLocaleString('en-IN')}`}  sub={`₹${(month.expenses || 0).toLocaleString('en-IN')} expenses`} icon={Activity}  gradient={month.net_profit >= 0 ? 'purple' : 'red'} />
        <StatCard label="Stock Items"        value={inv.total_items || 0}                                    sub={inv.low_stock_count > 0 ? `⚠ ${inv.low_stock_count} low stock` : 'All stocked'} icon={Package} gradient={inv.low_stock_count > 0 ? 'amber' : 'green'} />
      </div>

      {/* ── Pending + Alerts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-indigo-100 rounded-lg flex items-center justify-center">
                <CheckSquare size={14} className="text-indigo-600" />
              </div>
              <h2 className="font-bold text-gray-900 text-sm">Pending AI Actions</h2>
            </div>
            <Link to="/approvals" className="text-xs text-indigo-600 font-semibold flex items-center gap-0.5 hover:text-indigo-800">
              View all <ArrowUpRight size={12} />
            </Link>
          </div>
          {(summary?.pending_actions || 0) > 0 ? (
            <div className="rounded-xl p-4 border" style={{ background: 'linear-gradient(135deg,#fef3c7,#fde68a)', borderColor: '#fcd34d' }}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-amber-400 rounded-xl flex items-center justify-center">
                  <Zap size={18} className="text-white" />
                </div>
                <div>
                  <p className="font-black text-amber-900 text-xl">{summary.pending_actions}</p>
                  <p className="text-amber-800 text-xs">action{summary.pending_actions !== 1 ? 's' : ''} waiting</p>
                </div>
              </div>
              <Link to="/approvals" className="flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600 text-white text-sm font-bold px-4 py-2.5 rounded-xl transition-colors w-full">
                <CheckSquare size={14} /> Review & Apply
              </Link>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="w-12 h-12 bg-emerald-100 rounded-2xl flex items-center justify-center mb-3">
                <CheckCircle size={22} className="text-emerald-600" />
              </div>
              <p className="text-sm font-semibold text-gray-600">All clear!</p>
              <p className="text-xs text-gray-400 mt-1">Run AI Check to get smart suggestions.</p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-red-100 rounded-lg flex items-center justify-center">
                <Bell size={14} className="text-red-600" />
              </div>
              <h2 className="font-bold text-gray-900 text-sm">
                Recent Alerts
                {alerts.length > 0 && <span className="ml-2 text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded-full font-bold align-middle">{alerts.length}</span>}
              </h2>
            </div>
            <Link to="/alerts" className="text-xs text-indigo-600 font-semibold flex items-center gap-0.5 hover:text-indigo-800">
              View all <ArrowUpRight size={12} />
            </Link>
          </div>
          {alerts.length > 0 ? (
            <div className="space-y-2">
              {alerts.map(alert => {
                const s = ALERT_STYLE[alert.alert_type] || ALERT_STYLE.daily_insight
                return (
                  <div key={alert.id} className={`flex items-start gap-2.5 px-3 py-2.5 rounded-xl border text-xs leading-relaxed ${s.bg} ${s.border} ${s.text}`}>
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${s.dot}`} />
                    {alert.message.length > 100 ? alert.message.slice(0, 100) + '…' : alert.message}
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center mb-3">
                <Bell size={22} className="text-blue-500" />
              </div>
              <p className="text-sm font-semibold text-gray-600">No new alerts</p>
              <p className="text-xs text-gray-400 mt-1">Run AI Check to analyse your shop.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="font-bold text-gray-800 text-sm mb-3">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <QuickAction to="/chat"         label="Talk to AI"      desc="Record sales & stock" gradient="from-indigo-500 to-blue-600"   icon={MessageSquare} />
          <QuickAction to="/inventory"    label="Add Stock"       desc="Log new purchase"     gradient="from-emerald-500 to-teal-600"  icon={Package}       />
          <QuickAction to="/analytics"    label="Revenue Advisor" desc="Earn more this month" gradient="from-purple-500 to-violet-600" icon={BarChart2}     />
          <QuickAction to="/customer-bot" label="Customer Bot"    desc="Share shop link"      gradient="from-amber-500 to-orange-500"  icon={Share2}        />
        </div>
      </div>

      {/* ── Bottom KPIs ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card text-center">
          <DollarSign size={20} className="mx-auto text-indigo-400 mb-2" />
          <p className="text-2xl font-black text-gray-900">₹{(inv.total_stock_value || 0).toLocaleString('en-IN')}</p>
          <p className="text-xs text-gray-500 mt-0.5">Total stock invested</p>
        </div>
        <div className="card text-center">
          <Activity size={20} className="mx-auto text-emerald-400 mb-2" />
          <p className="text-2xl font-black text-gray-900">₹{(month.revenue || 0).toLocaleString('en-IN')}</p>
          <p className="text-xs text-gray-500 mt-0.5">Month revenue</p>
        </div>
        <div className="card text-center">
          <CheckSquare size={20} className="mx-auto text-purple-400 mb-2" />
          <p className="text-2xl font-black text-gray-900">{summary?.pending_actions || 0}</p>
          <p className="text-xs text-gray-500 mt-0.5">Pending AI suggestions</p>
        </div>
      </div>
    </div>
  )
}
