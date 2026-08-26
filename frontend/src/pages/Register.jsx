import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Zap, User, Store, Phone, Lock, ArrowRight, MessageSquare } from 'lucide-react'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', shop_name: '', phone: '', password: '', whatsapp_number: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      await register(form)
      navigate('/onboarding')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed.')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-5/12 flex-col justify-center p-12 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #312e81 100%)' }}>
        <div className="absolute -top-20 -left-20 w-80 h-80 rounded-full opacity-10" style={{ background: 'radial-gradient(circle, #818cf8, transparent)' }} />
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
            <Zap size={20} className="text-white" />
          </div>
          <div>
            <p className="text-white font-black text-lg">Nexus-SMB Lite</p>
            <p className="text-indigo-400 text-xs tracking-wide">AI Workforce</p>
          </div>
        </div>
        <h2 className="text-3xl font-black text-white mb-4 leading-tight">
          Start your<br />
          <span style={{ background: 'linear-gradient(135deg, #818cf8, #c084fc)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            AI-powered shop
          </span>
        </h2>
        <p className="text-indigo-300 text-sm leading-relaxed mb-6">
          Set up in 2 minutes. Get instant AI assistance for inventory, sales tracking, and customer service.
        </p>
        <div className="space-y-3">
          {['Free to use during hackathon', 'No technical knowledge needed', 'Works in Tamil & English', 'Customer bot ready in seconds'].map(t => (
            <div key={t} className="flex items-center gap-2.5">
              <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
              </div>
              <p className="text-indigo-200 text-sm">{t}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center p-6 bg-slate-50 overflow-y-auto">
        <div className="w-full max-w-sm py-6">
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2.5 mb-8">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
              <Zap size={18} className="text-white" />
            </div>
            <p className="font-black text-gray-900">Nexus-SMB Lite</p>
          </div>

          <h2 className="text-2xl font-black text-gray-900 mb-1">Register your shop</h2>
          <p className="text-gray-500 text-sm mb-7">Takes less than 2 minutes</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Your Name</label>
                <div className="relative">
                  <User size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input className="input pl-9" placeholder="Ravi Kumar" value={form.name} onChange={set('name')} required />
                </div>
              </div>
              <div>
                <label className="label">Shop Name</label>
                <div className="relative">
                  <Store size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input className="input pl-9" placeholder="Ravi Stores" value={form.shop_name} onChange={set('shop_name')} required />
                </div>
              </div>
            </div>

            <div>
              <label className="label">Phone Number</label>
              <div className="relative">
                <Phone size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input className="input pl-9" type="tel" placeholder="9876543210" value={form.phone} onChange={set('phone')} required />
              </div>
            </div>

            <div>
              <label className="label">
                WhatsApp Number
                <span className="text-gray-400 font-normal ml-1">(optional, for alerts)</span>
              </label>
              <div className="relative">
                <MessageSquare size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input className="input pl-9" type="tel" placeholder="Same as phone or different" value={form.whatsapp_number} onChange={set('whatsapp_number')} />
              </div>
            </div>

            <div>
              <label className="label">Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input className="input pl-9" type="password" placeholder="Min 6 characters" value={form.password} onChange={set('password')} required minLength={6} />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm bg-red-50 border border-red-200 px-4 py-3 rounded-xl">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 font-bold py-3 rounded-xl text-white transition-all duration-150 disabled:opacity-60 text-sm"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: '0 4px 15px rgba(99,102,241,0.35)' }}
            >
              {loading ? 'Setting up your shop…' : <><span>Create Shop Account</span><ArrowRight size={16} /></>}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already registered?{' '}
            <Link to="/login" className="text-indigo-600 font-semibold hover:text-indigo-800 transition-colors">
              Sign in →
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
