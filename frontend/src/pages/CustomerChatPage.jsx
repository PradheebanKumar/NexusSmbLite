import { useState, useRef, useEffect } from 'react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Send, TrendingUp, Info, X, BarChart2, ShoppingCart, AlertCircle } from 'lucide-react'

const QUICK_MESSAGES = [
  'Do you have milk?',
  'What is the price of rice?',
  'Is sugar available?',
  'Do you have eggs?',
  'What items do you sell?',
  'Is apple available?',
  'Do you have bread?',
  'What is the price of toor dal?',
]

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-bold shrink-0">S</div>
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm border border-gray-100">
        <div className="flex gap-1 items-center h-4">
          {[0, 150, 300].map(d => (
            <div key={d} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

const INTENT_COLORS = {
  AVAILABILITY_CHECK: 'bg-blue-100 text-blue-700',
  PRICE_ENQUIRY:      'bg-purple-100 text-purple-700',
  GREETING:           'bg-green-100 text-green-700',
  THANKS:             'bg-teal-100 text-teal-700',
  COMPLAINT:          'bg-red-100 text-red-700',
  OUT_OF_SCOPE:       'bg-gray-100 text-gray-600',
  BULK_ORDER:         'bg-orange-100 text-orange-700',
  MULTIPLE_ITEMS:     'bg-indigo-100 text-indigo-700',
  UNKNOWN:            'bg-gray-100 text-gray-500',
}

function Message({ msg }) {
  const isUser = msg.role === 'user'
  const time = new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  if (isUser) {
    return (
      <div className="flex justify-end mb-3">
        <div className="max-w-[75%]">
          <div className="bg-green-500 text-white rounded-2xl rounded-br-sm px-4 py-2.5 shadow-sm">
            <p className="text-sm leading-relaxed">{msg.text}</p>
          </div>
          <p className="text-right text-xs text-gray-400 mt-1 mr-1">{time}</p>
        </div>
      </div>
    )
  }
  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-bold shrink-0">S</div>
      <div className="max-w-[75%]">
        <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-2.5 shadow-sm border border-gray-100">
          <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{msg.text}</p>
        </div>
        {/* ML intent badge */}
        {msg.intent && msg.modelReady && (
          <div className="flex items-center gap-1.5 mt-1 ml-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${INTENT_COLORS[msg.intent] || 'bg-gray-100 text-gray-500'}`}>
              {msg.intent.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-gray-400">{Math.round((msg.confidence || 0) * 100)}% conf</span>
            {msg.usedMl && <span className="text-xs text-green-600 font-medium">· ML reply</span>}
          </div>
        )}
        <p className="text-xs text-gray-400 mt-0.5 ml-1">{time}</p>
      </div>
    </div>
  )
}

// ── Demand Signals Side Panel ────────────────────────────────────────────────
function DemandPanel({ signals, onClose }) {
  return (
    <div className="w-72 bg-white border-l border-gray-200 flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 bg-orange-50 border-b border-orange-100">
        <div className="flex items-center gap-2">
          <TrendingUp size={16} className="text-orange-600" />
          <span className="font-semibold text-sm text-orange-800">Demand Signals</span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={16} /></button>
      </div>

      <div className="p-3 bg-orange-50 border-b border-orange-100">
        <p className="text-xs text-orange-700">
          Items customers asked for but weren't in stock. Stock these to earn more!
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {signals.length === 0 ? (
          <div className="text-center py-10 px-4">
            <ShoppingCart size={28} className="mx-auto mb-2 text-gray-300" />
            <p className="text-sm text-gray-400">No demand signals yet.</p>
            <p className="text-xs text-gray-400 mt-1">Try asking "Is apple available?" below.</p>
          </div>
        ) : (
          signals.map((s, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3 border-b border-gray-50 hover:bg-gray-50">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${
                s.count >= 5 ? 'bg-red-500' : s.count >= 3 ? 'bg-orange-400' : 'bg-yellow-400'
              }`}>
                {s.count}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-800 truncate">{s.product}</p>
                <p className="text-xs text-gray-400">
                  {s.count} request{s.count > 1 ? 's' : ''}
                  {s.last_requested ? ` · ${new Date(s.last_requested).toLocaleDateString('en-IN')}` : ''}
                </p>
              </div>
              {s.count >= 3 && (
                <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-medium shrink-0">Hot</span>
              )}
            </div>
          ))
        )}
      </div>

      {signals.length > 0 && (
        <div className="p-3 border-t border-gray-100 bg-green-50">
          <p className="text-xs text-green-700 font-medium">
            💡 Add these to inventory → customers already want them!
          </p>
        </div>
      )}
    </div>
  )
}

// ── How it Works Info Box ─────────────────────────────────────────────────────
function HowItWorks({ onClose }) {
  return (
    <div className="bg-blue-50 border-b border-blue-200 px-4 py-3">
      <div className="flex items-start gap-2">
        <Info size={15} className="text-blue-500 mt-0.5 shrink-0" />
        <div className="flex-1">
          <p className="text-xs font-semibold text-blue-800 mb-1">How this works</p>
          <div className="text-xs text-blue-700 space-y-0.5">
            <p>1. Customer types a question (like on WhatsApp)</p>
            <p>2. <strong>Custom ML classifier</strong> detects intent instantly (98.9% accuracy)</p>
            <p>3. Simple intents (hi/thanks/timing) → instant reply, no API cost</p>
            <p>4. Product questions → AI checks your <strong>live inventory</strong> & answers</p>
            <p>5. If item unavailable → <strong>demand signal logged</strong> (right panel)</p>
          </div>
        </div>
        <button onClick={onClose} className="text-blue-400 hover:text-blue-600 shrink-0"><X size={14} /></button>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function CustomerChatPage() {
  const { owner } = useAuth()
  const [messages, setMessages]       = useState([])
  const [input, setInput]             = useState('')
  const [typing, setTyping]           = useState(false)
  const [showInfo, setShowInfo]       = useState(true)
  const [showPanel, setShowPanel]     = useState(true)
  const [signals, setSignals]         = useState([])
  const bottomRef = useRef()
  const inputRef  = useRef()

  // Load demand signals
  const loadSignals = () => {
    api.get('/whatsapp/demand-signals')
      .then(r => setSignals(r.data || []))
      .catch(() => {})
  }

  useEffect(() => {
    loadSignals()
    // Greeting
    setMessages([{
      role: 'bot',
      text: `Hello! 👋 Welcome to ${owner?.shop_name || 'our shop'}!\n\nI can help you with:\n• Product availability & prices\n• Stock information\n• What we sell\n\nWhat can I get for you today?`,
      ts: Date.now(),
    }])
  }, [owner])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg || typing) return

    setInput('')
    setShowInfo(false)
    setMessages(prev => [...prev, { role: 'user', text: msg, ts: Date.now() }])
    setTyping(true)

    try {
      const res = await api.post('/whatsapp/simulate', { message: msg })
      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.data.reply,
        ts: Date.now(),
        intent: res.data.ml_intent,
        confidence: res.data.ml_confidence,
        usedMl: res.data.used_ml,
        modelReady: res.data.model_ready,
      }])
      // Reload demand signals after each message
      loadSignals()
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: 'Sorry, something went wrong. Is the backend running?',
        ts: Date.now(),
      }])
    } finally {
      setTyping(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="flex h-screen overflow-hidden">

      {/* ── Chat area ── */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* WhatsApp-style header */}
        <div className="bg-green-700 text-white px-4 py-3 flex items-center gap-3 shadow-md">
          <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center font-bold text-lg shrink-0">
            {owner?.shop_name?.[0] || 'S'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm truncate">{owner?.shop_name || 'Shop Bot'}</p>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-green-300 rounded-full animate-pulse" />
              <p className="text-xs text-green-200">AI Customer Bot • Online</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowPanel(p => !p)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-xs font-medium transition-colors ${
                showPanel ? 'bg-orange-500 text-white' : 'bg-green-600 text-green-100 hover:bg-green-600'
              }`}
            >
              <BarChart2 size={12} />
              Demand {signals.length > 0 && `(${signals.length})`}
            </button>
            <button onClick={() => setShowInfo(p => !p)}
              className="p-1.5 rounded-full hover:bg-green-600 transition-colors">
              <Info size={16} />
            </button>
          </div>
        </div>

        {/* Info banner */}
        {showInfo && <HowItWorks onClose={() => setShowInfo(false)} />}

        {/* Chat messages with WhatsApp wallpaper */}
        <div className="flex-1 overflow-y-auto px-4 py-4"
          style={{ background: 'repeating-linear-gradient(45deg,#e5ddd5 0,#e5ddd5 2px,#d9d0c8 2px,#d9d0c8 4px)' }}>
          <div className="flex justify-center mb-4">
            <span className="bg-white/70 text-gray-500 text-xs px-3 py-1 rounded-full shadow-sm">Today</span>
          </div>
          {messages.map((msg, i) => <Message key={i} msg={msg} />)}
          {typing && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Quick chips */}
        <div className="bg-white border-t border-gray-200 px-3 pt-2 pb-1">
          <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
            {QUICK_MESSAGES.map(q => (
              <button key={q} onClick={() => sendMessage(q)} disabled={typing}
                className="whitespace-nowrap text-xs bg-green-50 border border-green-200 text-green-700 rounded-full px-3 py-1.5 hover:bg-green-100 transition-colors shrink-0 disabled:opacity-40">
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Input bar */}
        <div className="bg-gray-200 px-3 py-2 flex items-end gap-2">
          <div className="flex-1 bg-white rounded-3xl px-4 py-2.5 shadow-sm flex items-end">
            <textarea ref={inputRef} rows={1} value={input}
              onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
              disabled={typing} placeholder="Type a message..."
              className="flex-1 resize-none outline-none text-sm text-gray-800 bg-transparent max-h-24 leading-relaxed"
              style={{ scrollbarWidth: 'none' }} />
          </div>
          <button onClick={() => sendMessage()} disabled={!input.trim() || typing}
            className={`w-11 h-11 rounded-full flex items-center justify-center shadow-md transition-all ${
              input.trim() && !typing ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-400 cursor-not-allowed'
            }`}>
            <Send size={18} className="text-white" />
          </button>
        </div>
      </div>

      {/* ── Demand Signals Side Panel ── */}
      {showPanel && (
        <DemandPanel signals={signals} onClose={() => setShowPanel(false)} />
      )}
    </div>
  )
}
