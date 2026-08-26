import { useState, useEffect } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import {
  TrendingUp, TrendingDown, Target, Megaphone,
  AlertTriangle, CheckCircle, Package, DollarSign,
  Loader, ArrowRight, Zap, Copy, Check, Activity,
  ShieldCheck, RefreshCw, ChevronRight
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts'

const COLORS = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899']
const fmt    = (n) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })
const fmtDec = (n) => Number(n || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

// ─────────────────────────────────────────────────────────────────────────────
// Shared components
// ─────────────────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub, color = 'blue', icon: Icon, prefix = '₹' }) {
  const c = {
    blue:   'bg-blue-50 text-blue-700 border-blue-100',
    green:  'bg-green-50 text-green-700 border-green-100',
    red:    'bg-red-50 text-red-700 border-red-100',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-100',
    gray:   'bg-gray-50 text-gray-700 border-gray-100',
    purple: 'bg-purple-50 text-purple-700 border-purple-100',
  }[color] || 'bg-blue-50 text-blue-700 border-blue-100'
  return (
    <div className={`rounded-xl p-4 border ${c}`}>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-medium opacity-70">{label}</p>
        {Icon && <Icon size={16} className="opacity-50" />}
      </div>
      <p className="text-2xl font-bold">{prefix}{fmt(value)}</p>
      {sub && <p className="text-xs opacity-60 mt-1">{sub}</p>}
    </div>
  )
}

function EmptyState({ icon: Icon = Package, text, sub }) {
  return (
    <div className="text-center py-16 text-gray-400">
      <Icon size={36} className="mx-auto mb-3 opacity-30" />
      <p className="font-medium text-gray-500">{text}</p>
      {sub && <p className="text-sm mt-1">{sub}</p>}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 1: P&L Overview
// ─────────────────────────────────────────────────────────────────────────────
function OverviewTab({ pnl, trend, salesSummary, expenses, days }) {
  const pieData = pnl ? [
    { name: 'Stock cost', value: pnl.cost_of_goods_sold },
    { name: 'Expenses',   value: pnl.total_expenses },
    { name: 'Profit',     value: Math.max(0, pnl.net_profit) },
  ].filter(d => d.value > 0) : []

  const expBreakdown = expenses?.breakdown || []

  return (
    <div className="space-y-6">
      {!pnl ? <EmptyState text="No data" sub="Record some sales first." /> : <>

        {/* KPI row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard label="Revenue"    value={pnl.total_revenue}        sub={`Last ${days} days`}       color="blue"  icon={TrendingUp}   />
          <StatCard label="Stock Cost" value={pnl.cost_of_goods_sold}   sub="Cost of goods sold"        color="gray"  icon={Package}      />
          <StatCard label="Expenses"   value={pnl.total_expenses}        sub="Rent, electricity etc."    color="yellow" icon={DollarSign}  />
          <StatCard label="Net Profit" value={pnl.net_profit}            sub={`${pnl.profit_margin_pct}% margin`}
            color={pnl.net_profit >= 0 ? 'green' : 'red'} icon={pnl.net_profit >= 0 ? TrendingUp : TrendingDown} />
        </div>

        {/* Profit banner */}
        <div className={`rounded-xl p-4 border-2 flex items-center gap-3 ${pnl.is_profitable ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          {pnl.is_profitable
            ? <CheckCircle size={22} className="text-green-600 shrink-0" />
            : <AlertTriangle size={22} className="text-red-600 shrink-0" />}
          <div>
            <p className="font-semibold text-gray-800">
              {pnl.is_profitable
                ? `You made ₹${fmt(pnl.net_profit)} profit in ${days} days`
                : `You are ₹${fmt(Math.abs(pnl.net_profit))} in loss over ${days} days`}
            </p>
            <p className="text-sm text-gray-500 mt-0.5">
              Revenue ₹{fmt(pnl.total_revenue)} − stock cost ₹{fmt(pnl.cost_of_goods_sold)} − expenses ₹{fmt(pnl.total_expenses)} = ₹{fmt(pnl.net_profit)}
            </p>
          </div>
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {/* Revenue trend */}
          {trend?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-700 mb-3 text-sm">Daily Revenue & Profit</h3>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="day" tick={{ fontSize: 10 }} interval={Math.floor(trend.length / 5)} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `₹${v}`} width={50} />
                  <Tooltip formatter={(v, n) => [`₹${fmt(v)}`, n === 'revenue' ? 'Revenue' : 'Profit']} />
                  <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="profit"  stroke="#10b981" strokeWidth={2} dot={false} strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
              <div className="flex gap-4 mt-2 text-xs text-gray-400">
                <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-blue-500 inline-block" /> Revenue</span>
                <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-green-500 inline-block border-dashed" /> Profit</span>
              </div>
            </div>
          )}

          {/* Where revenue goes */}
          {pieData.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-700 mb-3 text-sm">Where does revenue go?</h3>
              <div className="flex justify-center">
                <PieChart width={240} height={170}>
                  <Pie data={pieData} cx={120} cy={75} innerRadius={40} outerRadius={65} paddingAngle={3} dataKey="value">
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                  </Pie>
                  <Legend iconSize={10} formatter={v => <span className="text-xs text-gray-600">{v}</span>} />
                  <Tooltip formatter={v => `₹${fmt(v)}`} />
                </PieChart>
              </div>
            </div>
          )}

          {/* Top sellers bar */}
          {salesSummary?.top_sellers?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-700 mb-3 text-sm">Top Selling Items</h3>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={salesSummary.top_sellers.slice(0, 6)} layout="vertical">
                  <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={v => `₹${v}`} />
                  <YAxis dataKey="item" type="category" tick={{ fontSize: 11 }} width={90} />
                  <Tooltip formatter={v => [`₹${fmt(v)}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Expense breakdown */}
          {expBreakdown.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-700 mb-3 text-sm">Expense Breakdown</h3>
              <div className="space-y-2">
                {expBreakdown.map(e => (
                  <div key={e.type}>
                    <div className="flex justify-between text-xs mb-0.5">
                      <span className="text-gray-600 capitalize">{e.type}</span>
                      <span className="font-medium text-gray-700">₹{fmt(e.amount)} <span className="text-gray-400">({e.pct}%)</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${e.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </>}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 2: Business Health Score
// ─────────────────────────────────────────────────────────────────────────────
function HealthScoreTab() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/analytics/health-score')
      .then(r => setData(r.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-20"><Loader size={24} className="animate-spin mx-auto text-blue-500" /></div>
  if (!data)   return <EmptyState text="Could not load health score" />

  const gradeColor = { A: 'text-green-600', B: 'text-blue-600', C: 'text-yellow-600', D: 'text-red-600' }[data.grade] || 'text-gray-600'
  const bgColor    = { A: 'bg-green-50 border-green-200', B: 'bg-blue-50 border-blue-200', C: 'bg-yellow-50 border-yellow-200', D: 'bg-red-50 border-red-200' }[data.grade]
  const dimLabels  = { profitability: 'Profitability', sales_trend: 'Sales Trend', inventory: 'Inventory Health', cash_flow: 'Cash Flow', demand_match: 'Demand Match' }
  const dimColors  = { profitability: '#3b82f6', sales_trend: '#10b981', inventory: '#f59e0b', cash_flow: '#8b5cf6', demand_match: '#ef4444' }

  return (
    <div className="space-y-5">
      {/* Main score card */}
      <div className={`rounded-2xl border-2 p-6 ${bgColor}`}>
        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className={`text-7xl font-black ${gradeColor}`}>{data.grade}</div>
            <div className="text-3xl font-bold text-gray-700 mt-1">{data.score}<span className="text-lg text-gray-400">/100</span></div>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-800 mb-1">Business Health Score</h2>
            <p className="text-gray-600">{data.summary}</p>
            {/* Score bar */}
            <div className="mt-4">
              <div className="w-full bg-white/60 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-3 rounded-full transition-all duration-1000 ${data.score >= 75 ? 'bg-green-500' : data.score >= 55 ? 'bg-blue-500' : data.score >= 35 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${data.score}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0 — Critical</span><span>35</span><span>55</span><span>75 — Excellent</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dimension breakdown */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-4">Score Breakdown</h3>
        <div className="space-y-4">
          {Object.entries(data.dimensions).map(([key, val]) => {
            const max = data.max_scores[key]
            const pct = Math.round(val / max * 100)
            return (
              <div key={key}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700">{dimLabels[key]}</span>
                  <span className="text-gray-500">{val.toFixed(0)} / {max} pts</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                  <div className="h-2.5 rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: dimColors[key] }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Tips */}
      <div className="space-y-3">
        <h3 className="font-semibold text-gray-700">Action Items</h3>
        {data.tips.map((tip, i) => (
          <div key={i} className={`rounded-xl border p-4 flex gap-3 ${
            tip.priority === 'high'   ? 'bg-red-50 border-red-200' :
            tip.priority === 'medium' ? 'bg-yellow-50 border-yellow-200' :
            'bg-green-50 border-green-200'
          }`}>
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 mt-0.5 ${
              tip.priority === 'high' ? 'bg-red-500' : tip.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
            }`}>{i + 1}</div>
            <div>
              <p className="text-sm font-semibold text-gray-800">{tip.area}</p>
              <p className="text-sm text-gray-600 mt-0.5">{tip.tip}</p>
            </div>
            <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full shrink-0 self-start ${
              tip.priority === 'high' ? 'bg-red-100 text-red-700' : tip.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'
            }`}>{tip.priority}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 3: Stock Recovery
// ─────────────────────────────────────────────────────────────────────────────
function ItemCard({ item }) {
  const isLoss = item.status === 'loss', isProfit = item.status === 'profit', isClose = item.status === 'close'
  const bg   = isLoss ? 'bg-red-50 border-red-200' : isProfit ? 'bg-green-50 border-green-200' : isClose ? 'bg-yellow-50 border-yellow-200' : 'bg-white border-gray-200'
  const bar  = isLoss ? 'bg-red-400' : isProfit ? 'bg-green-500' : isClose ? 'bg-yellow-400' : 'bg-blue-400'
  const badge = isLoss ? { t: 'Loss', c: 'bg-red-100 text-red-700' } : isProfit ? { t: 'Recovered', c: 'bg-green-100 text-green-700' } : isClose ? { t: 'Almost', c: 'bg-yellow-100 text-yellow-700' } : { t: 'In progress', c: 'bg-blue-100 text-blue-700' }
  return (
    <div className={`rounded-xl border-2 p-4 ${bg}`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-bold text-gray-900">{item.item}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            Cost <strong>₹{item.cost_price}</strong> → Sell <strong>₹{item.selling_price}</strong>
            <span className={`ml-2 font-semibold ${item.margin_pct >= 20 ? 'text-green-600' : item.margin_pct >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>{item.margin_pct}% margin</span>
          </p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-semibold ${badge.c}`}>{badge.t}</span>
      </div>
      {!isLoss && item.units_to_recover != null && (
        <>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Sold: <strong>{item.sold_this_month} {item.unit}</strong></span>
            <span>Target: <strong>{item.units_to_recover} {item.unit}</strong></span>
          </div>
          <div className="w-full bg-white/70 rounded-full h-2.5 mb-3 overflow-hidden">
            <div className={`h-2.5 rounded-full ${bar}`} style={{ width: `${item.pct_recovered}%` }} />
          </div>
        </>
      )}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="bg-white/60 rounded-lg py-2"><p className="text-xs text-gray-400">Invested</p><p className="text-sm font-bold text-gray-700">₹{fmt(item.stock_investment)}</p></div>
        <div className="bg-white/60 rounded-lg py-2"><p className="text-xs text-gray-400">If sold out</p><p className="text-sm font-bold text-green-600">+₹{fmt(item.potential_profit)}</p></div>
        <div className="bg-white/60 rounded-lg py-2"><p className="text-xs text-gray-400">ROI</p><p className={`text-sm font-bold ${item.roi_pct >= 20 ? 'text-green-600' : 'text-gray-600'}`}>{item.roi_pct}%</p></div>
      </div>
      <p className="text-xs text-gray-500 mt-3 leading-relaxed">{item.insight}</p>
    </div>
  )
}

function StockRecoveryTab({ bep }) {
  if (!bep) return <EmptyState text="Loading..." />
  return (
    <div className="space-y-5">
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
        <p className="font-semibold mb-1">What is Stock Recovery?</p>
        <p>When you buy stock (e.g. 20kg rice at ₹55 = ₹1100 invested), the progress bar shows how much of that investment you've recovered through sales. Once 100% → everything you earn is <strong>pure profit</strong>.</p>
      </div>
      <div className={`rounded-xl border-2 p-4 ${bep.shop_is_covering_costs ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
        <div className="flex items-center gap-3">
          {bep.shop_is_covering_costs
            ? <CheckCircle size={22} className="text-green-600 shrink-0" />
            : <AlertTriangle size={22} className="text-red-600 shrink-0" />}
          <div>
            <p className="font-semibold text-gray-800">
              Need <span className="text-blue-700">₹{fmt(bep.daily_breakeven_revenue)}/day</span> to cover expenses. Your avg: <span className={bep.shop_is_covering_costs ? 'text-green-700' : 'text-red-700'}>₹{fmt(bep.avg_daily_revenue)}/day</span>
            </p>
            <p className="text-sm text-gray-500">
              {bep.shop_is_covering_costs ? 'Covering fixed costs.' : `Need ₹${fmt(bep.daily_breakeven_revenue - bep.avg_daily_revenue)} more per day to break even.`}
            </p>
          </div>
        </div>
      </div>
      {bep.items?.length > 0
        ? <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">{bep.items.map(item => <ItemCard key={item.item} item={item} />)}</div>
        : <EmptyState text="Add inventory and record sales to see recovery progress." />}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 4: Revenue Advisor
// ─────────────────────────────────────────────────────────────────────────────
const ACTION_STYLES = {
  price_increase: { bg: 'bg-blue-50 border-blue-200',    badge: 'bg-blue-100 text-blue-700',    icon: '📈', label: 'Price Increase'  },
  discount:       { bg: 'bg-orange-50 border-orange-200', badge: 'bg-orange-100 text-orange-700', icon: '🏷', label: 'Discount / Clear' },
  promote:        { bg: 'bg-pink-50 border-pink-200',     badge: 'bg-pink-100 text-pink-700',    icon: '📣', label: 'Promote on WA'   },
  upsell:         { bg: 'bg-purple-50 border-purple-200', badge: 'bg-purple-100 text-purple-700', icon: '🔝', label: 'Upsell / Bundle' },
  stock_new:      { bg: 'bg-green-50 border-green-200',   badge: 'bg-green-100 text-green-700',  icon: '📦', label: 'Stock This Item' },
}

function RevenueAdvisorTab() {
  const { owner } = useAuth()
  const [gap, setGap]         = useState('')
  const [reason, setReason]   = useState('')
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [applied, setApplied] = useState({})
  const [applying, setApplying] = useState({})

  const run = async () => {
    if (!gap || isNaN(gap) || Number(gap) <= 0) { setError('Enter a valid amount (e.g. 2000)'); return }
    setError(''); setLoading(true); setResult(null); setApplied({})
    try {
      const res = await api.post('/analytics/revenue-advisor', { revenue_gap: Number(gap), reason })
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Analysis failed — check if backend is running.')
    } finally { setLoading(false) }
  }

  const applyPrice = async (action, idx) => {
    if (!action.item || !action.suggested_price) return
    setApplying(p => ({ ...p, [idx]: true }))
    try {
      const res = await api.post('/analytics/apply-price', {
        item_name: action.item,
        selling_price: action.suggested_price,
      })
      if (res.data.ok) {
        setApplied(p => ({ ...p, [idx]: `₹${res.data.old_price} → ₹${res.data.new_price}` }))
      } else {
        setApplied(p => ({ ...p, [idx]: 'Not found in inventory' }))
      }
    } catch {
      setApplied(p => ({ ...p, [idx]: 'Failed — update manually' }))
    } finally { setApplying(p => ({ ...p, [idx]: false })) }
  }

  return (
    <div className="space-y-5">
      {/* Input card */}
      <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-5 text-white">
        <div className="flex items-center gap-2 mb-1">
          <Zap size={20} className="text-yellow-300" />
          <h2 className="font-bold text-lg">Revenue Goal Advisor</h2>
        </div>
        <p className="text-blue-200 text-sm mb-5">
          Tell the AI how much more you need — it analyses your actual sales data and gives a step-by-step plan with exact prices.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-blue-200 block mb-1">I need ₹ ___ more this month</label>
            <div className="flex items-center bg-white/15 rounded-xl px-3 py-2.5 gap-2">
              <span className="font-bold text-xl">₹</span>
              <input type="number" value={gap} onChange={e => setGap(e.target.value)}
                placeholder="2000" className="bg-transparent font-bold text-xl outline-none w-full placeholder-blue-300"
                onKeyDown={e => e.key === 'Enter' && run()} />
            </div>
          </div>
          <div className="sm:col-span-1">
            <label className="text-xs text-blue-200 block mb-1">Why? (optional)</label>
            <input type="text" value={reason} onChange={e => setReason(e.target.value)}
              placeholder="e.g. need to pay rent"
              className="w-full bg-white/15 placeholder-blue-300 rounded-xl px-3 py-2.5 outline-none border border-white/20 text-sm" />
          </div>
          <div className="flex items-end">
            <button onClick={run} disabled={loading || !gap}
              className="w-full flex items-center justify-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-gray-900 font-bold px-5 py-2.5 rounded-xl transition-colors disabled:opacity-50">
              {loading ? <Loader size={16} className="animate-spin" /> : <Zap size={16} />}
              {loading ? 'Analysing...' : 'Get My Plan'}
            </button>
          </div>
        </div>
        {error && <p className="text-red-300 text-sm mt-3 bg-red-500/20 rounded-lg px-3 py-2">{error}</p>}
      </div>

      {loading && (
        <div className="text-center py-14">
          <Loader size={28} className="animate-spin mx-auto mb-3 text-blue-500" />
          <p className="font-medium text-gray-600">Analysing inventory and sales data...</p>
          <p className="text-sm text-gray-400 mt-1">Finding the best price changes for maximum impact</p>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="bg-white border-2 border-gray-100 rounded-xl p-4 shadow-sm">
            <div className="flex flex-wrap items-center gap-6">
              <div>
                <p className="text-xs text-gray-400 mb-0.5">Current monthly revenue</p>
                <p className="text-2xl font-bold text-gray-700">₹{fmt(result.current_monthly_revenue)}</p>
              </div>
              <ArrowRight size={20} className="text-gray-300" />
              <div>
                <p className="text-xs text-gray-400 mb-0.5">Target revenue</p>
                <p className="text-2xl font-bold text-green-700">₹{fmt(result.target_revenue)}</p>
              </div>
              <div className="ml-auto bg-green-50 border border-green-200 rounded-xl px-4 py-2 text-right">
                <p className="text-xs text-gray-400 mb-0.5">Expected gain from this plan</p>
                <p className="text-2xl font-bold text-green-700">+₹{fmt(result.total_expected_gain)}</p>
              </div>
            </div>
          </div>

          {/* Summary text */}
          <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
            <p className="text-sm text-blue-800">{result.summary}</p>
          </div>

          {result.warning && (
            <div className="flex items-start gap-2 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 text-sm text-yellow-800">
              <AlertTriangle size={15} className="shrink-0 mt-0.5" />
              {result.warning}
            </div>
          )}

          {/* No actions — show setup message */}
          {(!result.actions || result.actions.length === 0) && (
            <div className="text-center py-10 bg-gray-50 rounded-xl border border-gray-200">
              <Package size={32} className="mx-auto text-gray-300 mb-2" />
              <p className="text-gray-600 font-medium">Add products and record some sales first</p>
              <p className="text-gray-400 text-sm mt-1">The advisor needs sales data to suggest specific price changes.</p>
            </div>
          )}

          {/* Action cards */}
          {result.actions?.map((action, i) => {
            const style = ACTION_STYLES[action.type] || ACTION_STYLES.price_increase
            const isApplied = !!applied[i]
            const isApplying = !!applying[i]
            return (
              <div key={i} className={`rounded-xl border-2 p-4 ${style.bg}`}>
                <div className="flex items-start gap-3">
                  <div className="text-2xl shrink-0 mt-0.5">{style.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="font-bold text-gray-900 text-base">#{action.rank} {action.item}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.badge}`}>{style.label}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        action.confidence === 'high' ? 'bg-green-100 text-green-700' :
                        action.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-500'
                      }`}>{action.confidence} confidence</span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{action.reason}</p>
                    {action.how_to && (
                      <div className="text-xs bg-white/70 border border-gray-200 rounded-lg px-3 py-2 mb-3 text-gray-700">
                        <span className="font-semibold text-gray-500">Do now: </span>{action.how_to}
                      </div>
                    )}
                    <div className="flex items-center gap-3 flex-wrap">
                      {action.current_price > 0 && <span className="text-sm text-gray-400 line-through">₹{action.current_price}</span>}
                      {action.suggested_price > 0 && <span className="font-bold text-gray-900">→ ₹{action.suggested_price}</span>}
                      <span className="text-sm font-semibold text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded-lg">
                        +₹{fmt(action.expected_extra_revenue)} expected
                      </span>
                    </div>
                  </div>
                  {/* Apply button */}
                  <div className="shrink-0">
                    {isApplied ? (
                      <div className="text-center">
                        <div className="flex items-center gap-1 text-green-600 text-xs font-medium">
                          <Check size={14} /> Applied
                        </div>
                        <p className="text-xs text-gray-400 mt-0.5">{applied[i]}</p>
                      </div>
                    ) : ['price_increase', 'discount'].includes(action.type) && action.suggested_price > 0 ? (
                      <button onClick={() => applyPrice(action, i)} disabled={isApplying}
                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg transition-colors font-medium disabled:opacity-50 flex items-center gap-1">
                        {isApplying ? <Loader size={12} className="animate-spin" /> : <Check size={12} />}
                        {isApplying ? 'Applying...' : 'Apply Price'}
                      </button>
                    ) : action.type === 'promote' ? (
                      <a
                        href={`https://wa.me/?text=${encodeURIComponent(`Special offer on ${action.item}! Ask us for price.\nChat with us: ${window.location.origin}/shop/${owner?.id || ''}`)}`}
                        target="_blank" rel="noopener noreferrer"
                        className="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg transition-colors font-medium flex items-center gap-1">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                        Promote
                      </a>
                    ) : null}
                  </div>
                </div>
              </div>
            )
          })}

          <p className="text-xs text-gray-400 text-center">All actions also saved to Approvals page for review.</p>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 5: Ad Generator
// ─────────────────────────────────────────────────────────────────────────────
function AdGeneratorTab({ ownerId }) {
  const [inventory, setInventory] = useState([])
  const [item, setItem]           = useState('')
  const [adType, setAdType]       = useState('whatsapp')
  const [offerPct, setOfferPct]   = useState('')
  const [note, setNote]           = useState('')
  const [result, setResult]       = useState(null)
  const [loading, setLoading]     = useState(false)
  const [copied, setCopied]       = useState(false)

  // Build the public shop chat link so customers can tap and chat directly
  const shopUrl = ownerId ? `${window.location.origin}/shop/${ownerId}` : ''

  useEffect(() => { api.get('/inventory/').then(r => setInventory(r.data || [])) }, [])

  const generate = async () => {
    if (!item) return
    setLoading(true); setResult(null)
    try {
      const res = await api.post('/analytics/generate-ad', {
        item_name: item, ad_type: adType,
        offer_pct: offerPct ? Number(offerPct) : null,
        custom_note: note || null,
      })
      setResult(res.data)
    } catch (e) { alert(e.response?.data?.detail || 'Generation failed') }
    finally { setLoading(false) }
  }

  const fullAdText = () => {
    const text = result?.ad_text || ''
    if (shopUrl && adType === 'whatsapp') {
      return `${text}\n\nOrder online: ${shopUrl}`
    }
    return text
  }

  const copy = () => {
    navigator.clipboard.writeText(fullAdText())
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  const typeLabels = { whatsapp: 'WhatsApp Message', poster_caption: 'Poster Caption', sms: 'SMS (160 chars)' }
  const typeIcons  = { whatsapp: '💬', poster_caption: '🖼', sms: '📱' }

  return (
    <div className="space-y-5">
      <div className="card">
        <div className="flex items-center gap-2 mb-1">
          <Megaphone size={18} className="text-orange-500" />
          <h2 className="font-bold text-gray-800">Ad & Offer Content Generator</h2>
        </div>
        <p className="text-sm text-gray-500 mb-5">AI writes the ad for you in real shop-owner language. Copy and send on WhatsApp or print as a poster.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="label">Product</label>
            <select className="input" value={item} onChange={e => setItem(e.target.value)}>
              <option value="">Select item...</option>
              {inventory.map(i => <option key={i.id} value={i.item_name}>{i.item_name} — ₹{i.selling_price}/{i.unit}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Ad Type</label>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(typeLabels).map(([v, l]) => (
                <button key={v} onClick={() => setAdType(v)}
                  className={`text-xs py-2 px-1 rounded-lg border font-medium transition-colors text-center ${
                    adType === v ? 'bg-orange-500 text-white border-orange-500' : 'bg-white text-gray-600 border-gray-200 hover:border-orange-300'
                  }`}>
                  {typeIcons[v]} {l.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Discount % <span className="text-gray-400 font-normal">(optional)</span></label>
            <input type="number" className="input" placeholder="e.g. 10" value={offerPct} onChange={e => setOfferPct(e.target.value)} />
          </div>
          <div>
            <label className="label">Extra note <span className="text-gray-400 font-normal">(optional)</span></label>
            <input type="text" className="input" placeholder='e.g. "fresh stock arrived today"' value={note} onChange={e => setNote(e.target.value)} />
          </div>
        </div>

        <button onClick={generate} disabled={!item || loading}
          className="btn-primary flex items-center gap-2">
          {loading ? <Loader size={15} className="animate-spin" /> : <Megaphone size={15} />}
          {loading ? 'Writing...' : 'Generate Ad'}
        </button>
      </div>

      {result && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-gray-500 uppercase">{typeIcons[result.type]} {typeLabels[result.type]} · {result.item}</span>
            <div className="flex items-center gap-2">
              <button onClick={copy} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium px-2 py-1 rounded-lg hover:bg-blue-50">
                {copied ? <><Check size={12} /> Copied!</> : <><Copy size={12} /> Copy</>}
              </button>
              {result.type === 'whatsapp' && (
                <a
                  href={`https://wa.me/?text=${encodeURIComponent(fullAdText())}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs bg-green-600 hover:bg-green-700 text-white font-medium px-2.5 py-1.5 rounded-lg transition-colors"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                  Share on WhatsApp
                </a>
              )}
            </div>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            <p className="text-gray-800 whitespace-pre-wrap text-sm leading-relaxed">{result.ad_text}</p>
            {shopUrl && adType === 'whatsapp' && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-400 mb-1">Auto-appended shop link (customers click to chat):</p>
                <p className="text-xs text-blue-600 font-medium break-all">Order online: {shopUrl}</p>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3 mt-3">
            <p className="text-xs text-gray-400 flex-1">Also saved to Approvals page — approve it there to keep record.</p>
            <button onClick={generate} className="btn-secondary text-sm">Regenerate</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────
export default function AnalyticsPage() {
  const { owner } = useAuth()
  const [pnl, setPnl]               = useState(null)
  const [bep, setBep]               = useState(null)
  const [trend, setTrend]           = useState(null)
  const [salesSummary, setSalesSummary] = useState(null)
  const [expenses, setExpenses]     = useState(null)
  const [days, setDays]             = useState(14)
  const [loading, setLoading]       = useState(true)
  const [tab, setTab]               = useState('overview')

  const load = () => {
    setLoading(true)
    Promise.all([
      api.get(`/analytics/profit-loss?days=${days}`),
      api.get('/analytics/break-even'),
      api.get(`/analytics/daily-trend?days=${days}`),
      api.get(`/sales/summary?days=${days}`),
      api.get(`/analytics/expense-breakdown?days=${days}`),
    ]).then(([p, b, t, s, e]) => {
      setPnl(p.data); setBep(b.data); setTrend(t.data); setSalesSummary(s.data); setExpenses(e.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [days])

  const tabs = [
    { id: 'overview',  label: 'P&L',         icon: TrendingUp   },
    { id: 'health',    label: 'Health Score', icon: ShieldCheck  },
    { id: 'stock',     label: 'Stock',        icon: Package      },
    { id: 'advisor',   label: 'Revenue',      icon: Zap          },
    { id: 'ads',       label: 'Ad Gen',       icon: Megaphone    },
  ]

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics & Growth</h1>
          <p className="text-sm text-gray-400 mt-0.5">Real numbers from your inventory and sales</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
          <select className="input w-auto text-sm" value={days} onChange={e => setDays(Number(e.target.value))}>
            {[7, 14, 30, 90].map(d => <option key={d} value={d}>Last {d} days</option>)}
          </select>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 flex-1 py-2 px-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap min-w-0 justify-center ${
              tab === t.id ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
            }`}>
            <t.icon size={14} />
            {t.label}
          </button>
        ))}
      </div>

      {loading && (tab === 'overview' || tab === 'stock') ? (
        <div className="text-center py-20">
          <Loader size={24} className="animate-spin mx-auto text-blue-500 mb-3" />
          <p className="text-gray-400">Loading analytics...</p>
        </div>
      ) : (
        <>
          {tab === 'overview' && <OverviewTab pnl={pnl} trend={trend} salesSummary={salesSummary} expenses={expenses} days={days} />}
          {tab === 'health'   && <HealthScoreTab />}
          {tab === 'stock'    && <StockRecoveryTab bep={bep} />}
          {tab === 'advisor'  && <RevenueAdvisorTab />}
          {tab === 'ads'      && <AdGeneratorTab ownerId={owner?.id} />}
        </>
      )}
    </div>
  )
}
