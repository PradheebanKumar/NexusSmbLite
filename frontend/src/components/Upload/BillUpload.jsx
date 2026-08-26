import { useState, useRef } from 'react'
import api from '../../api/client'
import { Upload, Camera, CheckCircle, Edit2, Loader, X, AlertCircle } from 'lucide-react'

const UNITS = ['units', 'kg', 'g', 'litre', 'ml', 'pack', 'box', 'dozen', 'piece']

export default function BillUpload({ onDone }) {
  const [stage, setStage] = useState('idle') // idle | uploading | preview | applying | done
  const [preview, setPreview] = useState(null)
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [imagePreview, setImagePreview] = useState(null)
  const fileRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    setError('')
    setStage('uploading')
    setImagePreview(URL.createObjectURL(file))

    const form = new FormData()
    form.append('file', file)
    form.append('apply_immediately', 'false')

    try {
      const res = await api.post('/upload/bill', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setPreview(res.data)
      setItems(res.data.items || [])
      setStage('preview')
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to read bill. Try a clearer photo.')
      setStage('idle')
    }
  }

  const applyStock = async () => {
    setStage('applying')
    setError('')
    try {
      // Send confirmed items to backend
      const payload = items.map(item => ({
        item_name: item.item_name,
        quantity: parseFloat(item.quantity) || 0,
        unit: item.unit || 'units',
        cost_price: parseFloat(item.cost_price) || 0,
        suggested_selling_price: parseFloat(item.suggested_selling_price) || null,
      })).filter(i => i.item_name && i.quantity > 0 && i.cost_price > 0)

      await api.post('/upload/bill/confirm', payload)
      setStage('done')
      setTimeout(() => { onDone?.(); setStage('idle'); setItems([]); setImagePreview(null) }, 2000)
    } catch (e) {
      setError('Error applying stock: ' + (e.response?.data?.detail || e.message))
      setStage('preview')
    }
  }

  const updateItem = (idx, field, value) => {
    setItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item))
  }

  const removeItem = (idx) => {
    setItems(prev => prev.filter((_, i) => i !== idx))
  }

  if (stage === 'done') {
    return (
      <div className="flex items-center justify-center gap-3 py-8 text-green-600">
        <CheckCircle size={24} />
        <span className="font-medium">Stock updated successfully!</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      {stage === 'idle' && (
        <div
          onClick={() => fileRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) }}
          className="border-2 border-dashed border-blue-200 rounded-xl p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
        >
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={e => handleFile(e.target.files[0])} capture="environment" />
          <div className="flex justify-center gap-4 mb-3">
            <Camera size={28} className="text-blue-400" />
            <Upload size={28} className="text-blue-400" />
          </div>
          <p className="font-medium text-gray-700">Take a photo or upload the bill</p>
          <p className="text-sm text-gray-400 mt-1">JPG, PNG, WebP • AI reads and extracts items automatically</p>
        </div>
      )}

      {stage === 'uploading' && (
        <div className="text-center py-10">
          {imagePreview && <img src={imagePreview} alt="bill" className="max-h-48 mx-auto rounded-lg mb-4 object-contain" />}
          <Loader size={28} className="animate-spin text-blue-500 mx-auto mb-2" />
          <p className="text-gray-600 font-medium">Reading your bill with AI...</p>
          <p className="text-gray-400 text-sm">Extracting items, quantities and prices</p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 bg-red-50 text-red-700 px-4 py-3 rounded-xl text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {stage === 'preview' && items.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="font-semibold text-gray-800">
                Found {items.length} items — review & confirm
              </p>
              {preview?.supplier && (
                <p className="text-xs text-gray-400">From: {preview.supplier} {preview.bill_date ? `| ${preview.bill_date}` : ''}</p>
              )}
            </div>
            {imagePreview && (
              <img src={imagePreview} alt="bill" className="w-12 h-12 rounded object-cover border" />
            )}
          </div>

          <div className="border border-gray-100 rounded-xl overflow-hidden">
            <div className="grid grid-cols-12 gap-1 bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
              <div className="col-span-4">Item</div>
              <div className="col-span-2">Qty</div>
              <div className="col-span-1">Unit</div>
              <div className="col-span-2">Cost ₹</div>
              <div className="col-span-2">Sell ₹</div>
              <div className="col-span-1"></div>
            </div>
            <div className="divide-y divide-gray-50 max-h-72 overflow-y-auto">
              {items.map((item, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-1 px-3 py-2 items-center hover:bg-gray-50">
                  <div className="col-span-4">
                    <input className="input text-xs py-1 px-2" value={item.item_name || ''}
                      onChange={e => updateItem(idx, 'item_name', e.target.value)} />
                  </div>
                  <div className="col-span-2">
                    <input className="input text-xs py-1 px-2" type="number" value={item.quantity || ''}
                      onChange={e => updateItem(idx, 'quantity', e.target.value)} />
                  </div>
                  <div className="col-span-1">
                    <select className="input text-xs py-1 px-1" value={item.unit || 'units'}
                      onChange={e => updateItem(idx, 'unit', e.target.value)}>
                      {UNITS.map(u => <option key={u}>{u}</option>)}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <input className="input text-xs py-1 px-2" type="number" value={item.cost_price || ''}
                      onChange={e => updateItem(idx, 'cost_price', e.target.value)} />
                  </div>
                  <div className="col-span-2">
                    <input className="input text-xs py-1 px-2" type="number"
                      value={item.suggested_selling_price || ''}
                      onChange={e => updateItem(idx, 'suggested_selling_price', e.target.value)} />
                  </div>
                  <div className="col-span-1 flex justify-center">
                    <button onClick={() => removeItem(idx)} className="text-gray-300 hover:text-red-400 p-0.5">
                      <X size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-3 bg-amber-50 rounded-lg px-3 py-2 text-xs text-amber-700">
            Selling prices are auto-suggested. Edit any price before confirming.
          </div>

          <div className="flex gap-3 mt-4">
            <button onClick={() => { setStage('idle'); setItems([]); setImagePreview(null) }}
              className="btn-secondary flex-1">
              Upload different bill
            </button>
            <button onClick={applyStock} disabled={stage === 'applying'}
              className="btn-primary flex-1">
              {stage === 'applying' ? 'Updating stock...' : `Confirm & Update Stock (${items.length} items)`}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
