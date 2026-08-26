import { useState, useEffect } from 'react'
import api from '../api/client'
import BillUpload from '../components/Upload/BillUpload'
import { Plus, Edit2, Trash2, AlertTriangle, Package, Upload } from 'lucide-react'

function AddItemModal({ onClose, onSaved, editItem }) {
  const [form, setForm] = useState(editItem || {
    item_name: '', quantity: '', unit: 'units',
    cost_price: '', selling_price: '', low_stock_threshold: 10
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [priceSuggestion, setPriceSuggestion] = useState(null)

  const fetchPriceSuggestion = async (name, cost) => {
    if (!name || !cost || cost <= 0) return
    try {
      const res = await api.get(`/upload/price-suggestion?item_name=${encodeURIComponent(name)}&cost_price=${cost}`)
      setPriceSuggestion(res.data)
      if (!form.selling_price) {
        setForm(f => ({ ...f, selling_price: res.data.suggested_price }))
      }
    } catch {}
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (editItem) {
        await api.put(`/inventory/${editItem.id}`, form)
      } else {
        await api.post('/inventory/', form)
      }
      onSaved()
      onClose()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save item')
    } finally {
      setLoading(false)
    }
  }

  const profit = form.selling_price && form.cost_price
    ? (parseFloat(form.selling_price) - parseFloat(form.cost_price)).toFixed(2)
    : null

  const margin = form.selling_price && form.cost_price && parseFloat(form.selling_price) > 0
    ? ((parseFloat(form.selling_price) - parseFloat(form.cost_price)) / parseFloat(form.selling_price) * 100).toFixed(1)
    : null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
        <h2 className="text-lg font-semibold mb-5">{editItem ? 'Edit Item' : 'Add New Item'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-2">
              <label className="label">Item Name</label>
              <input className="input" placeholder="Milk packets" required
                value={form.item_name}
                onChange={e => setForm({ ...form, item_name: e.target.value })} />
            </div>
            <div>
              <label className="label">Unit</label>
              <select className="input" value={form.unit}
                onChange={e => setForm({ ...form, unit: e.target.value })}>
                {['units', 'kg', 'g', 'litre', 'ml', 'pack', 'box', 'dozen', 'piece'].map(u =>
                  <option key={u}>{u}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Quantity</label>
            <input className="input" type="number" min="0" step="0.1" placeholder="100" required
              value={form.quantity}
              onChange={e => setForm({ ...form, quantity: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Cost Price (₹)</label>
              <input className="input" type="number" min="0" step="0.01" placeholder="20" required
                value={form.cost_price}
                onChange={e => {
                  setForm({ ...form, cost_price: e.target.value })
                  if (form.item_name) fetchPriceSuggestion(form.item_name, parseFloat(e.target.value))
                }}
                onBlur={() => fetchPriceSuggestion(form.item_name, parseFloat(form.cost_price))} />
            </div>
            <div>
              <label className="label">Selling Price (₹)</label>
              <input className="input" type="number" min="0" step="0.01" placeholder="30" required
                value={form.selling_price}
                onChange={e => setForm({ ...form, selling_price: e.target.value })} />
            </div>
          </div>
          {priceSuggestion && !editItem && (
            <div className="bg-indigo-50 rounded-lg px-4 py-2 text-xs text-indigo-700">
              AI suggestion: ₹{priceSuggestion.suggested_price} — {priceSuggestion.reasoning}
            </div>
          )}
          {profit !== null && (
            <div className="bg-blue-50 rounded-lg px-4 py-2 flex justify-between text-sm">
              <span className="text-gray-600">Profit per unit</span>
              <span className={`font-semibold ${parseFloat(profit) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ₹{profit} ({margin}%)
              </span>
            </div>
          )}
          <div>
            <label className="label">Low Stock Alert Threshold</label>
            <input className="input" type="number" min="0"
              value={form.low_stock_threshold}
              onChange={e => setForm({ ...form, low_stock_threshold: e.target.value })} />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" className="btn-primary flex-1" disabled={loading}>
              {loading ? 'Saving...' : 'Save Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function AddStockModal({ item, onClose, onSaved }) {
  const [qty, setQty] = useState('')
  const [cost, setCost] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/inventory/add-stock', {
        item_name: item.item_name,
        quantity: parseFloat(qty),
        cost_price: cost ? parseFloat(cost) : undefined
      })
      onSaved()
      onClose()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6 shadow-xl">
        <h2 className="text-lg font-semibold mb-4">Add Stock — {item.item_name}</h2>
        <p className="text-sm text-gray-500 mb-4">Current: {item.quantity} {item.unit}</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Quantity to Add</label>
            <input className="input" type="number" min="0.1" step="0.1" required
              value={qty} onChange={e => setQty(e.target.value)} />
          </div>
          <div>
            <label className="label">New Cost Price (₹) <span className="text-gray-400">— optional</span></label>
            <input className="input" type="number" min="0" step="0.01" placeholder={item.cost_price}
              value={cost} onChange={e => setCost(e.target.value)} />
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancel</button>
            <button type="submit" className="btn-primary flex-1" disabled={loading}>
              {loading ? 'Adding...' : 'Add Stock'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function InventoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [showBillUpload, setShowBillUpload] = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [addStockItem, setAddStockItem] = useState(null)
  const [search, setSearch] = useState('')

  const load = () => {
    setLoading(true)
    api.get('/inventory/').then(res => setItems(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const deleteItem = async (id) => {
    if (!confirm('Delete this item?')) return
    await api.delete(`/inventory/${id}`)
    load()
  }

  const filtered = items.filter(i => i.item_name.toLowerCase().includes(search.toLowerCase()))

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
        <div className="flex gap-2">
          <button onClick={() => setShowBillUpload(true)} className="btn-secondary flex items-center gap-2">
            <Upload size={18} /> Upload Bill
          </button>
          <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2">
            <Plus size={18} /> Add Item
          </button>
        </div>
      </div>

      <div className="mb-4">
        <input className="input max-w-xs" placeholder="Search items..."
          value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Item', 'Stock', 'Cost ₹', 'Sell ₹', 'Profit', 'Margin', 'Status', 'Actions'].map(h => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filtered.map(item => (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{item.item_name}</td>
                  <td className="px-4 py-3 text-gray-600">{item.quantity} <span className="text-gray-400">{item.unit}</span></td>
                  <td className="px-4 py-3 text-gray-600">₹{item.cost_price}</td>
                  <td className="px-4 py-3 text-gray-600">₹{item.selling_price}</td>
                  <td className="px-4 py-3">
                    <span className={item.profit_per_unit >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                      ₹{item.profit_per_unit}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{item.margin_pct}%</td>
                  <td className="px-4 py-3">
                    {item.is_dead_stock ? <span className="badge-red">Dead stock</span> :
                     item.is_slow_mover ? <span className="badge-yellow">Slow</span> :
                     item.is_low_stock ? <span className="badge-yellow flex items-center gap-1"><AlertTriangle size={11} />Low</span> :
                     <span className="badge-green">Good</span>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button onClick={() => setAddStockItem(item)}
                        className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded hover:bg-green-100">
                        +Stock
                      </button>
                      <button onClick={() => setEditItem(item)} className="text-gray-400 hover:text-blue-600 p-1">
                        <Edit2 size={15} />
                      </button>
                      <button onClick={() => deleteItem(item.id)} className="text-gray-400 hover:text-red-500 p-1">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={8} className="px-4 py-12 text-center text-gray-400">
                  <Package size={32} className="mx-auto mb-2 text-gray-300" />
                  No items found
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showBillUpload && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold">Upload Purchase Bill</h2>
              <button onClick={() => setShowBillUpload(false)} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
            </div>
            <BillUpload onDone={() => { setShowBillUpload(false); load() }} />
          </div>
        </div>
      )}
      {showAdd && <AddItemModal onClose={() => setShowAdd(false)} onSaved={load} />}
      {editItem && <AddItemModal editItem={editItem} onClose={() => setEditItem(null)} onSaved={load} />}
      {addStockItem && <AddStockModal item={addStockItem} onClose={() => setAddStockItem(null)} onSaved={load} />}
    </div>
  )
}
