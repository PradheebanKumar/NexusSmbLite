import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import {
  Link2, Copy, Check, TrendingUp, ShoppingCart,
  Users, ExternalLink, RefreshCw, Flame, Star, Info
} from 'lucide-react'

export default function ShareShopPage() {
  const { owner } = useAuth()
  const [signals, setSignals] = useState([])
  const [copied, setCopied]   = useState(false)
  const [loading, setLoading] = useState(true)

  const shopUrl = `${window.location.origin}/shop/${owner?.id}`

  const loadSignals = () => {
    setLoading(true)
    api.get('/whatsapp/demand-signals')
      .then(r => setSignals(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadSignals() }, [])

  const copyLink = () => {
    navigator.clipboard.writeText(shopUrl)
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  const MIN_COUNT = 2
  const visible    = signals.filter(s => s.count >= MIN_COUNT)
  const total      = visible.reduce((s, x) => s + x.count, 0)
  const hot        = visible.filter(s => s.count >= 3).length

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-5">

      {/* ── Share card ── */}
      <div className="rounded-2xl overflow-hidden border border-gray-100 shadow-sm bg-white">
        {/* Header strip */}
        <div className="px-6 py-5 flex items-center gap-4" style={{ background: 'linear-gradient(135deg, #059669, #0d9488)' }}>
          <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center shrink-0">
            <Link2 size={22} className="text-white" />
          </div>
          <div>
            <p className="text-white font-bold text-base">Your Shop Chat Link</p>
            <p className="text-emerald-100 text-xs mt-0.5">Share with customers — no login needed for them</p>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* URL display */}
          <div className="flex items-center gap-3 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3">
            <p className="flex-1 text-sm text-gray-700 font-mono break-all">{shopUrl}</p>
            <button
              onClick={copyLink}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 shrink-0 ${
                copied
                  ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <a href={shopUrl} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 text-white text-sm font-bold px-4 py-2.5 rounded-xl transition-all hover:opacity-90"
              style={{ background: 'linear-gradient(135deg, #059669, #0d9488)' }}>
              <ExternalLink size={15} /> Preview as Customer
            </a>
            <div className="flex-1 bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-2.5 flex items-start gap-2">
              <Info size={13} className="text-indigo-500 shrink-0 mt-0.5" />
              <p className="text-xs text-indigo-700 leading-relaxed">
                <strong>Tip:</strong> Generate a QR code at qr-code-generator.com and stick it at your counter!
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── How it works ── */}
      <div className="card">
        <h2 className="font-bold text-gray-900 mb-4 text-sm">How it works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { n: '1', text: 'Customer opens your link on their phone', color: 'bg-indigo-100 text-indigo-700' },
            { n: '2', text: 'They enter their name — no password needed', color: 'bg-blue-100 text-blue-700' },
            { n: '3', text: 'They ask about availability, prices, deals', color: 'bg-emerald-100 text-emerald-700' },
            { n: '4', text: 'AI answers from your live inventory in real-time', color: 'bg-purple-100 text-purple-700' },
            { n: '5', text: 'Discounts you set appear as highlighted deals', color: 'bg-orange-100 text-orange-700' },
            { n: '6', text: 'Popular products appear below as demand signals', color: 'bg-red-100 text-red-700' },
          ].map(({ n, text, color }) => (
            <div key={n} className="flex items-start gap-3">
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-black shrink-0 mt-0.5 ${color}`}>{n}</span>
              <p className="text-sm text-gray-600 leading-relaxed">{text}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Demand signals ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-orange-100 rounded-lg flex items-center justify-center">
              <TrendingUp size={14} className="text-orange-600" />
            </div>
            <h2 className="font-bold text-gray-900 text-sm">Customer Demand Signals</h2>
          </div>
          <button onClick={loadSignals}
            className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 px-2.5 py-1.5 rounded-lg hover:bg-gray-100 transition-colors font-medium">
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 divide-x divide-gray-100 border-b border-gray-100">
          {[
            { label: 'Trending Products', value: visible.length, icon: ShoppingCart, color: 'text-blue-500' },
            { label: 'Total Requests',    value: total,          icon: Users,        color: 'text-emerald-500' },
            { label: 'Hot Items (3+)',    value: hot,            icon: Flame,        color: 'text-orange-500' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="py-4 text-center">
              <Icon size={16} className={`mx-auto mb-1.5 ${color}`} />
              <p className="text-2xl font-black text-gray-900">{value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>

        {/* List */}
        <div>
          {loading ? (
            <div className="space-y-3 p-4">
              {[1,2,3].map(i => <div key={i} className="skeleton h-12 rounded-xl" />)}
            </div>
          ) : visible.length === 0 ? (
            <div className="py-14 text-center px-6">
              <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                <ShoppingCart size={24} className="text-gray-300" />
              </div>
              <p className="text-gray-600 font-semibold text-sm">No trending products yet</p>
              <p className="text-gray-400 text-xs mt-1.5 max-w-xs mx-auto">
                Products appear here once <strong>2+ customers</strong> ask about them — so you only see real demand.
              </p>
            </div>
          ) : (
            visible.map((s, i) => {
              const isHot  = s.count >= 3 && s.count < 5
              const isFire = s.count >= 5
              return (
                <div key={i} className="flex items-center gap-4 px-6 py-3.5 border-b border-gray-50 last:border-0 hover:bg-gray-50/60 transition-colors">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-black text-white shrink-0 ${
                    isFire ? 'bg-red-500' : isHot ? 'bg-orange-400' : 'bg-blue-400'
                  }`}>
                    {s.count}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{s.product}</p>
                    <p className="text-xs text-gray-400">
                      {s.count} customer{s.count > 1 ? 's' : ''} asked
                      {s.last_requested ? ` · ${new Date(s.last_requested).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}` : ''}
                    </p>
                  </div>
                  {isFire && (
                    <span className="flex items-center gap-1 text-xs bg-red-50 border border-red-200 text-red-600 px-2.5 py-1 rounded-full font-bold shrink-0">
                      <Flame size={10} /> Stock it!
                    </span>
                  )}
                  {isHot && !isFire && (
                    <span className="flex items-center gap-1 text-xs bg-orange-50 border border-orange-200 text-orange-600 px-2.5 py-1 rounded-full font-bold shrink-0">
                      <Star size={10} /> Hot
                    </span>
                  )}
                </div>
              )
            })
          )}
        </div>

        {visible.length > 0 && (
          <div className="px-6 py-3 bg-amber-50 border-t border-amber-100">
            <p className="text-xs text-amber-800">
              <strong>Stock it!</strong> = 5+ customers asked — high chance of sale if you stock it now.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
