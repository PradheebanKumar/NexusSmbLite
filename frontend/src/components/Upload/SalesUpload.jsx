import { useState, useRef } from 'react'
import api from '../../api/client'
import { Upload, Camera, CheckCircle, Loader, X, AlertCircle, FileText } from 'lucide-react'

export default function SalesUpload({ onDone }) {
  const [stage, setStage] = useState('idle')
  const [items, setItems] = useState([])
  const [textInput, setTextInput] = useState('')
  const [inputMode, setInputMode] = useState('image') // image | text
  const [error, setError] = useState('')
  const [saleDate, setSaleDate] = useState(
    new Date(Date.now() - 86400000).toISOString().split('T')[0] // yesterday
  )
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
    form.append('sale_date', saleDate)

    try {
      const res = await api.post('/upload/sales', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setItems(res.data.items || [])
      setStage('preview')
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not read. Try a clearer image.')
      setStage('idle')
    }
  }

  const handleText = async () => {
    if (!textInput.trim()) return
    setError('')
    setStage('uploading')

    const form = new FormData()
    form.append('text_data', textInput)
    form.append('apply_immediately', 'false')
    form.append('sale_date', saleDate)

    try {
      const res = await api.post('/upload/sales', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setItems(res.data.items || [])
      setStage('preview')
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not extract sales data.')
      setStage('idle')
    }
  }

  const applySales = async () => {
    setStage('applying')
    try {
      const form = new FormData()
      form.append('text_data', items.map(i =>
        `sold ${i.quantity_sold} ${i.item_name}${i.selling_price ? ` at ${i.selling_price}` : ''}`
      ).join(', '))
      form.append('apply_immediately', 'true')
      form.append('sale_date', saleDate)
      await api.post('/upload/sales', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setStage('done')
      setTimeout(() => { onDone?.(); setStage('idle'); setItems([]); setTextInput(''); setImagePreview(null) }, 2000)
    } catch (e) {
      // Fallback: use sales API directly
      try {
        await api.post('/sales/', {
          items: items.filter(i => i.item_name && i.quantity_sold).map(i => ({
            item_name: i.item_name,
            quantity_sold: parseFloat(i.quantity_sold),
          })),
          date: new Date(saleDate).toISOString(),
        })
        setStage('done')
        setTimeout(() => { onDone?.(); setStage('idle'); setItems([]); setTextInput(''); setImagePreview(null) }, 2000)
      } catch (err) {
        setError('Error recording sales: ' + (err.response?.data?.detail || err.message))
        setStage('preview')
      }
    }
  }

  const updateItem = (idx, field, value) => {
    setItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item))
  }

  if (stage === 'done') {
    return (
      <div className="flex items-center justify-center gap-3 py-8 text-green-600">
        <CheckCircle size={24} />
        <span className="font-medium">Sales recorded!</span>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Date selector */}
      <div className="flex items-center gap-3">
        <label className="text-sm text-gray-600 font-medium whitespace-nowrap">Sales date:</label>
        <input type="date" className="input w-auto text-sm"
          value={saleDate} onChange={e => setSaleDate(e.target.value)} max={new Date().toISOString().split('T')[0]} />
      </div>

      {/* Mode toggle */}
      {stage === 'idle' && (
        <div className="flex gap-2">
          <button onClick={() => setInputMode('image')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              inputMode === 'image' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
            }`}>
            <Camera size={15} /> Photo / Image
          </button>
          <button onClick={() => setInputMode('text')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              inputMode === 'text' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
            }`}>
            <FileText size={15} /> Type / Paste Text
          </button>
        </div>
      )}

      {stage === 'idle' && inputMode === 'image' && (
        <div onClick={() => fileRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]) }}
          className="border-2 border-dashed border-green-200 rounded-xl p-8 text-center cursor-pointer hover:border-green-400 hover:bg-green-50 transition-colors">
          <input ref={fileRef} type="file" accept="image/*" className="hidden"
            onChange={e => handleFile(e.target.files[0])} capture="environment" />
          <Camera size={28} className="text-green-400 mx-auto mb-3" />
          <p className="font-medium text-gray-700">Photo of your sales register</p>
          <p className="text-sm text-gray-400 mt-1">Handwritten notebook, printed report, any format</p>
        </div>
      )}

      {stage === 'idle' && inputMode === 'text' && (
        <div>
          <textarea
            className="input resize-none"
            rows={5}
            placeholder={`Type what you sold today, e.g.:\n"sold 35 milk, 18 bread, 8 kg rice, 6 sugar packets, 15 curd"\n\nOr paste forwarded WhatsApp message from your assistant`}
            value={textInput}
            onChange={e => setTextInput(e.target.value)}
          />
          <button onClick={handleText} disabled={!textInput.trim()}
            className="btn-primary mt-3 w-full">
            Extract Sales Data
          </button>
        </div>
      )}

      {stage === 'uploading' && (
        <div className="text-center py-10">
          {imagePreview && <img src={imagePreview} alt="sales" className="max-h-40 mx-auto rounded-lg mb-4 object-contain" />}
          <Loader size={28} className="animate-spin text-green-500 mx-auto mb-2" />
          <p className="text-gray-600 font-medium">Reading sales data with AI...</p>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 bg-red-50 text-red-700 px-4 py-3 rounded-xl text-sm">
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {stage === 'preview' && items.length > 0 && (
        <div>
          <p className="font-semibold text-gray-800 mb-3">Found {items.length} items — review & confirm</p>
          <div className="border border-gray-100 rounded-xl overflow-hidden">
            <div className="grid grid-cols-12 bg-gray-50 px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
              <div className="col-span-5">Item</div>
              <div className="col-span-4">Qty Sold</div>
              <div className="col-span-2">Sell ₹</div>
              <div className="col-span-1"></div>
            </div>
            <div className="divide-y divide-gray-50 max-h-64 overflow-y-auto">
              {items.map((item, idx) => (
                <div key={idx} className="grid grid-cols-12 px-3 py-2 items-center gap-1">
                  <div className="col-span-5">
                    <input className="input text-xs py-1 px-2" value={item.item_name || ''}
                      onChange={e => updateItem(idx, 'item_name', e.target.value)} />
                  </div>
                  <div className="col-span-4">
                    <input className="input text-xs py-1 px-2" type="number" value={item.quantity_sold || ''}
                      onChange={e => updateItem(idx, 'quantity_sold', e.target.value)} />
                  </div>
                  <div className="col-span-2">
                    <input className="input text-xs py-1 px-2" type="number"
                      placeholder="auto"
                      value={item.selling_price || ''}
                      onChange={e => updateItem(idx, 'selling_price', e.target.value)} />
                  </div>
                  <div className="col-span-1 flex justify-center">
                    <button onClick={() => setItems(p => p.filter((_, i) => i !== idx))}
                      className="text-gray-300 hover:text-red-400 p-0.5"><X size={13} /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">Sell ₹ is optional — leave blank to use stored price</p>
          <div className="flex gap-3 mt-4">
            <button onClick={() => { setStage('idle'); setItems([]) }} className="btn-secondary flex-1">
              Try again
            </button>
            <button onClick={applySales} className="btn-primary flex-1">
              Record {items.length} items
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
