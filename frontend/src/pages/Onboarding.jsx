import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Plus, Trash2, ChevronRight, Package, ShoppingCart, CheckCircle } from 'lucide-react'

const UNIT_OPTIONS = ['units', 'kg', 'g', 'litre', 'ml', 'pack', 'box', 'dozen', 'piece']

const SAMPLE_PRODUCTS = [
  { item_name: 'Milk 500ml', quantity: 100, unit: 'pack', cost_price: 20, selling_price: 25 },
  { item_name: 'Bread 400g', quantity: 50, unit: 'pack', cost_price: 22, selling_price: 28 },
  { item_name: 'Rice (loose)', quantity: 42, unit: 'kg', cost_price: 42, selling_price: 55 },
  { item_name: 'Toor Dal', quantity: 10, unit: 'kg', cost_price: 95, selling_price: 115 },
  { item_name: 'Sugar 1kg', quantity: 30, unit: 'pack', cost_price: 43, selling_price: 48 },
]

const COMMON_ITEMS = [
  { item_name: 'Milk 500ml', cost_price: 20, selling_price: 25, unit: 'pack' },
  { item_name: 'Bread 400g', cost_price: 22, selling_price: 28, unit: 'pack' },
  { item_name: 'Parle-G 100g', cost_price: 5, selling_price: 5, unit: 'pack' },
  { item_name: 'Rice (loose)', cost_price: 42, selling_price: 55, unit: 'kg' },
  { item_name: 'Toor Dal', cost_price: 95, selling_price: 115, unit: 'kg' },
  { item_name: 'Sugar 1kg', cost_price: 43, selling_price: 48, unit: 'pack' },
  { item_name: 'Sunflower Oil 1L', cost_price: 110, selling_price: 135, unit: 'units' },
  { item_name: 'Tea Powder 250g', cost_price: 62, selling_price: 75, unit: 'pack' },
  { item_name: 'Coconut Oil 500ml', cost_price: 75, selling_price: 90, unit: 'units' },
  { item_name: 'Eggs', cost_price: 5.4, selling_price: 7, unit: 'piece' },
  { item_name: 'Colgate 100g', cost_price: 52, selling_price: 55, unit: 'units' },
  { item_name: 'Curd 200g', cost_price: 18, selling_price: 22, unit: 'pack' },
  { item_name: 'Butter 100g', cost_price: 55, selling_price: 58, unit: 'units' },
  { item_name: 'Surf Excel 500g', cost_price: 95, selling_price: 100, unit: 'pack' },
  { item_name: 'Bread Biscuit', cost_price: 10, selling_price: 10, unit: 'pack' },
]

function StockRow({ item, onChange, onRemove }) {
  return (
    <div className="grid grid-cols-12 gap-2 items-center py-2 border-b border-gray-50">
      <div className="col-span-3">
        <input className="input text-sm py-1.5" placeholder="Item name"
          value={item.item_name}
          onChange={e => onChange({ ...item, item_name: e.target.value })} />
      </div>
      <div className="col-span-2">
        <input className="input text-sm py-1.5" type="number" placeholder="Qty"
          value={item.quantity}
          onChange={e => onChange({ ...item, quantity: e.target.value })} />
      </div>
      <div className="col-span-2">
        <select className="input text-sm py-1.5" value={item.unit}
          onChange={e => onChange({ ...item, unit: e.target.value })}>
          {UNIT_OPTIONS.map(u => <option key={u}>{u}</option>)}
        </select>
      </div>
      <div className="col-span-2">
        <div className="relative">
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">₹</span>
          <input className="input text-sm py-1.5 pl-6" type="number" placeholder="Cost"
            value={item.cost_price}
            onChange={e => onChange({ ...item, cost_price: e.target.value })} />
        </div>
      </div>
      <div className="col-span-2">
        <div className="relative">
          <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">₹</span>
          <input className="input text-sm py-1.5 pl-6" type="number" placeholder="Sell"
            value={item.selling_price}
            onChange={e => onChange({ ...item, selling_price: e.target.value })} />
        </div>
      </div>
      <div className="col-span-1 flex justify-center">
        <button onClick={onRemove} className="text-gray-300 hover:text-red-400 transition-colors p-1">
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  )
}

function SaleRow({ item, onChange, onRemove }) {
  return (
    <div className="grid grid-cols-12 gap-2 items-center py-2 border-b border-gray-50">
      <div className="col-span-5">
        <input className="input text-sm py-1.5" placeholder="Item name"
          value={item.item_name}
          onChange={e => onChange({ ...item, item_name: e.target.value })} />
      </div>
      <div className="col-span-5">
        <input className="input text-sm py-1.5" type="number" placeholder="Qty sold yesterday"
          value={item.quantity_sold}
          onChange={e => onChange({ ...item, quantity_sold: e.target.value })} />
      </div>
      <div className="col-span-1 flex justify-center">
        <button onClick={onRemove} className="text-gray-300 hover:text-red-400 transition-colors p-1">
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  )
}

export default function Onboarding() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1) // 1=stock, 2=sales, 3=done
  const [stockItems, setStockItems] = useState(SAMPLE_PRODUCTS.map((p, i) => ({ ...p, id: i })))
  const [saleItems, setSaleItems] = useState([
    { id: 0, item_name: 'Milk 500ml', quantity_sold: 35 },
    { id: 1, item_name: 'Bread 400g', quantity_sold: 18 },
    { id: 2, item_name: 'Rice (loose)', quantity_sold: 8 },
  ])
  const [saving, setSaving] = useState(false)
  const [nextId, setNextId] = useState(100)

  const addStockItem = () => {
    setStockItems(prev => [...prev, { id: nextId, item_name: '', quantity: '', unit: 'units', cost_price: '', selling_price: '' }])
    setNextId(n => n + 1)
  }

  const addFromCommon = (common) => {
    const already = stockItems.find(s => s.item_name.toLowerCase() === common.item_name.toLowerCase())
    if (already) return
    setStockItems(prev => [...prev, { id: nextId, ...common, quantity: '' }])
    setNextId(n => n + 1)
  }

  const addSaleItem = () => {
    setSaleItems(prev => [...prev, { id: nextId, item_name: '', quantity_sold: '' }])
    setNextId(n => n + 1)
  }

  const saveStock = async () => {
    setSaving(true)
    const valid = stockItems.filter(i => i.item_name && i.quantity && i.cost_price && i.selling_price)
    try {
      for (const item of valid) {
        await api.post('/inventory/', {
          item_name: item.item_name,
          quantity: parseFloat(item.quantity),
          unit: item.unit,
          cost_price: parseFloat(item.cost_price),
          selling_price: parseFloat(item.selling_price),
          low_stock_threshold: 10,
        })
      }
      setStep(2)
    } catch (e) {
      alert('Error saving stock: ' + (e.response?.data?.detail || e.message))
    } finally {
      setSaving(false)
    }
  }

  const saveSales = async () => {
    setSaving(true)
    const valid = saleItems.filter(i => i.item_name && i.quantity_sold)
    try {
      if (valid.length > 0) {
        await api.post('/sales/', {
          items: valid.map(i => ({ item_name: i.item_name, quantity_sold: parseFloat(i.quantity_sold) })),
          date: new Date(Date.now() - 86400000).toISOString(), // yesterday
        })
      }
      setStep(3)
    } catch (e) {
      alert('Error saving sales: ' + (e.response?.data?.detail || e.message))
    } finally {
      setSaving(false)
    }
  }

  if (step === 3) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-10 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-5">
            <CheckCircle size={36} className="text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">You're all set!</h2>
          <p className="text-gray-500 mb-8">
            Your inventory and sales data are loaded. Your AI assistant is ready.
          </p>
          <button onClick={() => navigate('/')} className="btn-primary w-full py-3 text-base">
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">N</div>
            <span className="font-semibold text-gray-900">Nexus-SMB — Setup</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className={step >= 1 ? 'text-blue-600 font-medium' : ''}>1. Stock</span>
            <ChevronRight size={14} />
            <span className={step >= 2 ? 'text-blue-600 font-medium' : ''}>2. Yesterday's Sales</span>
            <ChevronRight size={14} />
            <span className={step >= 3 ? 'text-blue-600 font-medium' : ''}>3. Done</span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto p-6">
        {step === 1 && (
          <>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Package size={24} className="text-blue-600" /> Add Your Current Stock
              </h1>
              <p className="text-gray-500 mt-1">
                Enter what you have in your shop right now — quantity, what you paid (cost), and what you charge customers (selling price).
              </p>
            </div>

            {/* Quick add from common items */}
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-5">
              <p className="text-sm font-medium text-blue-800 mb-3">Quick add common items (click to add):</p>
              <div className="flex flex-wrap gap-2">
                {COMMON_ITEMS.map(item => {
                  const added = stockItems.find(s => s.item_name.toLowerCase() === item.item_name.toLowerCase())
                  return (
                    <button key={item.item_name}
                      onClick={() => addFromCommon(item)}
                      disabled={!!added}
                      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                        added
                          ? 'bg-green-100 border-green-200 text-green-700 cursor-default'
                          : 'bg-white border-blue-200 text-blue-700 hover:bg-blue-100'
                      }`}>
                      {added ? '✓ ' : '+ '}{item.item_name}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Table header */}
            <div className="card p-0 overflow-hidden">
              <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-gray-50 border-b border-gray-100">
                <div className="col-span-3 text-xs font-semibold text-gray-500 uppercase">Item Name</div>
                <div className="col-span-2 text-xs font-semibold text-gray-500 uppercase">Quantity</div>
                <div className="col-span-2 text-xs font-semibold text-gray-500 uppercase">Unit</div>
                <div className="col-span-2 text-xs font-semibold text-gray-500 uppercase">Cost ₹</div>
                <div className="col-span-2 text-xs font-semibold text-gray-500 uppercase">Sell ₹</div>
                <div className="col-span-1"></div>
              </div>
              <div className="px-4 divide-y divide-gray-50">
                {stockItems.map(item => (
                  <StockRow key={item.id} item={item}
                    onChange={updated => setStockItems(prev => prev.map(i => i.id === item.id ? updated : i))}
                    onRemove={() => setStockItems(prev => prev.filter(i => i.id !== item.id))} />
                ))}
              </div>
              <div className="px-4 py-3 border-t border-gray-100">
                <button onClick={addStockItem}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium">
                  <Plus size={16} /> Add another item
                </button>
              </div>
            </div>

            <div className="mt-4 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3 text-sm text-amber-800">
              <strong>Tip:</strong> For packaged goods with MRP printed (biscuits, chips), set Cost = what you paid distributor. Selling price = MRP printed on packet.
            </div>

            <div className="flex justify-between items-center mt-6">
              <button onClick={() => navigate('/')} className="text-sm text-gray-400 hover:text-gray-600">
                Skip setup → go to dashboard
              </button>
              <button onClick={saveStock} disabled={saving} className="btn-primary px-8 py-2.5">
                {saving ? 'Saving...' : 'Save Stock & Continue →'}
              </button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <ShoppingCart size={24} className="text-blue-600" /> Yesterday's Sales
              </h1>
              <p className="text-gray-500 mt-1">
                Enter how much you sold yesterday. This gives AI a starting point for trends and break-even analysis.
              </p>
            </div>

            <div className="card p-0 overflow-hidden">
              <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-gray-50 border-b border-gray-100">
                <div className="col-span-5 text-xs font-semibold text-gray-500 uppercase">Item Name</div>
                <div className="col-span-6 text-xs font-semibold text-gray-500 uppercase">Quantity Sold Yesterday</div>
                <div className="col-span-1"></div>
              </div>
              <div className="px-4 divide-y divide-gray-50">
                {saleItems.map(item => (
                  <SaleRow key={item.id} item={item}
                    onChange={updated => setSaleItems(prev => prev.map(i => i.id === item.id ? updated : i))}
                    onRemove={() => setSaleItems(prev => prev.filter(i => i.id !== item.id))} />
                ))}
              </div>
              <div className="px-4 py-3 border-t border-gray-100">
                <button onClick={addSaleItem}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium">
                  <Plus size={16} /> Add item
                </button>
              </div>
            </div>

            <div className="flex justify-between items-center mt-6">
              <button onClick={() => setStep(3)} className="text-sm text-gray-400 hover:text-gray-600">
                Skip — I'll enter sales later
              </button>
              <button onClick={saveSales} disabled={saving} className="btn-primary px-8 py-2.5">
                {saving ? 'Saving...' : 'Save & Finish →'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
