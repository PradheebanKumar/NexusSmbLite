import { useState, useEffect } from 'react'
import api from '../api/client'
import SalesUpload from '../components/Upload/SalesUpload'
import { Plus, ShoppingCart, Minus, Upload } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function SalesPage() {
  const [inventory, setInventory] = useState([])
  const [cart, setCart] = useState([])
  const [dailySales, setDailySales] = useState([])
  const [todaySales, setTodaySales] = useState(null)
  const [recording, setRecording] = useState(false)
  const [success, setSuccess] = useState('')
  const [activeTab, setActiveTab] = useState('record')
  const [showSalesUpload, setShowSalesUpload] = useState(false)

  useEffect(() => {
    api.get('/inventory/').then(res => setInventory(res.data))
    api.get('/sales/today').then(res => setTodaySales(res.data))
    api.get('/sales/daily?days=7').then(res => setDailySales(res.data))
  }, [])

  const addToCart = (item) => {
    setCart(prev => {
      const existing = prev.find(c => c.id === item.id)
      if (existing) return prev.map(c => c.id === item.id ? { ...c, qty: c.qty + 1 } : c)
      return [...prev, { ...item, qty: 1 }]
    })
  }

  const updateCartQty = (id, qty) => {
    if (qty <= 0) setCart(prev => prev.filter(c => c.id !== id))
    else setCart(prev => prev.map(c => c.id === id ? { ...c, qty } : c))
  }

  const recordSales = async () => {
    if (cart.length === 0) return
    setRecording(true)
    try {
      const items = cart.map(c => ({ item_name: c.item_name, quantity_sold: c.qty }))
      const res = await api.post('/sales/', { items })
      setCart([])
      setSuccess('Sales recorded successfully!')
      api.get('/sales/today').then(res => setTodaySales(res.data))
      api.get('/inventory/').then(res => setInventory(res.data))
      setTimeout(() => setSuccess(''), 3000)
    } catch (e) {
      alert('Error: ' + (e.response?.data?.detail || e.message))
    } finally {
      setRecording(false)
    }
  }

  const cartTotal = cart.reduce((sum, c) => sum + c.selling_price * c.qty, 0)

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Sales</h1>

      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-2">
          {['record', 'history'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
              activeTab === tab ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}>
            {tab === 'record' ? 'Record Sales' : 'Today\'s Summary'}
          </button>
        ))}
        </div>
        <button onClick={() => setShowSalesUpload(true)}
          className="btn-secondary flex items-center gap-2 text-sm">
          <Upload size={16} /> Upload Sales File
        </button>
      </div>

      {showSalesUpload && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-xl p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-semibold">Upload Sales Record</h2>
                <p className="text-sm text-gray-400 mt-0.5">Photo of register, typed list, or WhatsApp text</p>
              </div>
              <button onClick={() => setShowSalesUpload(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <SalesUpload onDone={() => {
              setShowSalesUpload(false)
              api.get('/sales/today').then(res => setTodaySales(res.data))
              api.get('/sales/daily?days=7').then(res => setDailySales(res.data))
              api.get('/inventory/').then(res => setInventory(res.data))
            }} />
          </div>
        </div>
      )}

      {activeTab === 'record' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Item selector */}
          <div className="lg:col-span-2 card">
            <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <ShoppingCart size={18} className="text-blue-600" /> Select Items Sold
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {inventory.map(item => (
                <button key={item.id} onClick={() => addToCart(item)}
                  disabled={item.quantity <= 0}
                  className={`text-left p-3 rounded-xl border transition-colors ${
                    item.quantity <= 0
                      ? 'border-gray-100 bg-gray-50 opacity-50 cursor-not-allowed'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-blue-50'
                  }`}>
                  <p className="font-medium text-sm text-gray-900 truncate">{item.item_name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">₹{item.selling_price} / {item.unit}</p>
                  <p className={`text-xs mt-1 ${item.is_low_stock ? 'text-orange-500' : 'text-gray-400'}`}>
                    Stock: {item.quantity}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Cart */}
          <div className="card">
            <h2 className="font-semibold text-gray-800 mb-4">Cart</h2>
            {cart.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-8">Click items to add to cart</p>
            ) : (
              <>
                <div className="space-y-3 mb-4">
                  {cart.map(item => (
                    <div key={item.id} className="flex items-center justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{item.item_name}</p>
                        <p className="text-xs text-gray-400">₹{item.selling_price} × {item.qty}</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button onClick={() => updateCartQty(item.id, item.qty - 1)}
                          className="w-7 h-7 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center">
                          <Minus size={12} />
                        </button>
                        <span className="w-8 text-center text-sm font-medium">{item.qty}</span>
                        <button onClick={() => updateCartQty(item.id, item.qty + 1)}
                          className="w-7 h-7 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center">
                          <Plus size={12} />
                        </button>
                      </div>
                      <span className="text-sm font-semibold text-right w-16">
                        ₹{(item.selling_price * item.qty).toFixed(0)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="border-t pt-3 mb-4">
                  <div className="flex justify-between font-semibold">
                    <span>Total</span>
                    <span className="text-blue-600">₹{cartTotal.toFixed(2)}</span>
                  </div>
                </div>
                {success && <p className="text-green-600 text-sm bg-green-50 px-3 py-2 rounded-lg mb-3">{success}</p>}
                <button onClick={recordSales} disabled={recording} className="btn-primary w-full">
                  {recording ? 'Recording...' : 'Record Sales'}
                </button>
                <button onClick={() => setCart([])} className="btn-secondary w-full mt-2 text-sm">
                  Clear Cart
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-6">
          {todaySales && (
            <div className="card">
              <h2 className="font-semibold mb-4">Today's Sales</h2>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="bg-blue-50 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-blue-700">₹{todaySales.total_revenue}</p>
                  <p className="text-xs text-blue-500 mt-1">Revenue</p>
                </div>
                <div className="bg-green-50 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-green-700">{todaySales.total_transactions}</p>
                  <p className="text-xs text-green-500 mt-1">Transactions</p>
                </div>
                <div className="bg-purple-50 rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-purple-700">{todaySales.sales?.length || 0}</p>
                  <p className="text-xs text-purple-500 mt-1">Line Items</p>
                </div>
              </div>
              {todaySales.sales?.length > 0 && (
                <div className="border-t pt-4 space-y-2">
                  {todaySales.sales.map((s, i) => (
                    <div key={i} className="flex justify-between text-sm text-gray-600">
                      <span>{s.item} × {s.quantity}</span>
                      <span className="font-medium">₹{s.amount}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {dailySales.length > 0 && (
            <div className="card">
              <h2 className="font-semibold mb-4">Last 7 Days Revenue</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={dailySales}>
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} tickFormatter={d => d.slice(5)} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => [`₹${v}`, 'Revenue']} />
                  <Bar dataKey="revenue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
