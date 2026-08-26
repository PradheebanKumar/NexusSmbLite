/**
 * PUBLIC customer chat page — no login needed.
 * ANY number of customers can use the same link simultaneously.
 *
 * /shop/1  → shows Owner 1's shop (owner 1 shares this link to customers)
 * /shop/2  → shows Owner 2's shop (completely separate inventory & bot)
 *
 * Each customer enters their name once per device (stored in localStorage).
 * "Change name" button lets a different customer use the same device/browser.
 */
import { useState, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { Send, X, Tag, ChevronDown, ChevronUp, Edit2 } from 'lucide-react'

// No auth headers — this is fully public
const publicApi = axios.create({ baseURL: 'http://localhost:8000/api' })

const INTENT_COLORS = {
  AVAILABILITY_CHECK: 'bg-blue-100 text-blue-600',
  PRICE_ENQUIRY:      'bg-purple-100 text-purple-600',
  GREETING:           'bg-green-100 text-green-600',
  THANKS:             'bg-teal-100 text-teal-600',
  COMPLAINT:          'bg-red-100 text-red-600',
  OUT_OF_SCOPE:       'bg-gray-100 text-gray-500',
  BULK_ORDER:         'bg-orange-100 text-orange-600',
  MULTIPLE_ITEMS:     'bg-indigo-100 text-indigo-600',
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function TypingIndicator({ shopName }) {
  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
        {shopName?.[0] || 'S'}
      </div>
      <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          {[0, 150, 300].map(d => (
            <div key={d} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: `${d}ms` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

function BotMessage({ msg, shopName }) {
  const time = new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white text-sm font-bold shrink-0">
        {shopName?.[0] || 'S'}
      </div>
      <div className="max-w-[78%]">
        <div className="bg-white rounded-2xl rounded-bl-sm px-4 py-2.5 shadow-sm">
          <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{msg.text}</p>
        </div>
        {msg.intent && msg.intent !== 'GREETING' && msg.intent !== 'THANKS' && (
          <span className={`inline-block text-[10px] px-1.5 py-0.5 rounded-full font-medium mt-1 ml-1 ${INTENT_COLORS[msg.intent] || 'bg-gray-100 text-gray-500'}`}>
            {msg.intent.replace(/_/g, ' ')}
          </span>
        )}
        <p className="text-[10px] text-gray-400 mt-0.5 ml-1">{time}</p>
      </div>
    </div>
  )
}

function UserMessage({ msg }) {
  const time = new Date(msg.ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
  return (
    <div className="flex justify-end mb-3">
      <div className="max-w-[78%]">
        <div className="bg-green-500 text-white rounded-2xl rounded-br-sm px-4 py-2.5 shadow-sm">
          <p className="text-sm leading-relaxed">{msg.text}</p>
        </div>
        <p className="text-right text-[10px] text-gray-400 mt-0.5 mr-1">{time}</p>
      </div>
    </div>
  )
}

// Name entry screen — shown to new customers and when "Change name" is clicked
function NameEntry({ shopName, deals, onSubmit }) {
  const [name, setName] = useState('')
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 px-4 py-8">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm text-center">

        {/* Shop avatar */}
        <div className="w-16 h-16 rounded-full bg-green-600 flex items-center justify-center text-white text-2xl font-bold mx-auto mb-3">
          {shopName?.[0] || 'S'}
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-0.5">{shopName}</h2>
        <p className="text-gray-500 text-sm mb-4">AI-powered customer assistant</p>

        {/* Active deals teaser */}
        {deals?.length > 0 && (
          <div className="bg-orange-50 border border-orange-200 rounded-xl px-3 py-2.5 mb-5 text-left">
            <p className="text-xs font-bold text-orange-700 mb-1.5 flex items-center gap-1">
              <Tag size={11} /> Today's Deals
            </p>
            {deals.slice(0, 3).map(d => (
              <div key={d.name} className="flex items-center justify-between text-xs mb-1">
                <span className="text-gray-700 font-medium">{d.name}</span>
                <span className="text-orange-600 font-bold">
                  Rs.{d.deal_price}/{d.unit}
                  <span className="ml-1 text-[10px] bg-orange-100 text-orange-700 px-1 rounded">{d.pct_off}% off</span>
                </span>
              </div>
            ))}
            <p className="text-[10px] text-orange-500 mt-1">Ask the bot for more details!</p>
          </div>
        )}

        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && name.trim() && onSubmit(name.trim())}
          placeholder="Enter your name to start"
          className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-green-500"
          autoFocus
        />
        <button
          onClick={() => name.trim() && onSubmit(name.trim())}
          disabled={!name.trim()}
          className="w-full bg-green-600 text-white rounded-xl py-3 text-sm font-semibold hover:bg-green-700 disabled:opacity-50 transition-colors"
        >
          Start Chat
        </button>
        <p className="text-xs text-gray-400 mt-3">Powered by Nexus-SMB AI</p>
      </div>
    </div>
  )
}

// Deals banner shown inside the chat
function DealsBanner({ deals, onAsk }) {
  const [expanded, setExpanded] = useState(true)
  if (!deals || deals.length === 0) return null
  return (
    <div className="mx-4 mb-3 bg-white rounded-2xl shadow-sm border border-orange-200 overflow-hidden">
      <button
        onClick={() => setExpanded(p => !p)}
        className="w-full flex items-center justify-between px-4 py-2.5 bg-orange-50 text-orange-700"
      >
        <div className="flex items-center gap-2">
          <Tag size={13} className="shrink-0" />
          <span className="text-xs font-bold">{deals.length} Special Offer{deals.length > 1 ? 's' : ''} Today!</span>
        </div>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>
      {expanded && (
        <div className="px-4 py-2">
          {deals.map(d => (
            <button
              key={d.name}
              onClick={() => onAsk(`Tell me about the offer on ${d.name}`)}
              className="w-full flex items-center justify-between py-2 border-b border-gray-100 last:border-0 hover:bg-orange-50 rounded-lg px-1 transition-colors"
            >
              <div className="text-left">
                <p className="text-sm font-semibold text-gray-800">{d.name}</p>
                <p className="text-xs text-gray-400">{d.stock} {d.unit} available</p>
              </div>
              <div className="text-right shrink-0 ml-3">
                <p className="text-xs text-gray-400 line-through">Rs.{d.original_price}/{d.unit}</p>
                <p className="text-sm font-bold text-orange-600">Rs.{d.deal_price}/{d.unit}</p>
                <span className="text-[10px] bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded-full font-medium">
                  {d.pct_off}% OFF
                </span>
              </div>
            </button>
          ))}
          <p className="text-[10px] text-gray-400 mt-2 text-center">Tap any deal to ask the bot</p>
        </div>
      )}
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function ShopChatPage() {
  const { ownerId } = useParams()
  const [shopInfo, setShopInfo]         = useState(null)
  const [deals, setDeals]               = useState([])
  const [loading, setLoading]           = useState(true)
  const [error, setError]               = useState('')
  const [customerName, setCustomerName] = useState('')
  const [messages, setMessages]         = useState([])
  const [input, setInput]               = useState('')
  const [typing, setTyping]             = useState(false)
  const [showProducts, setShowProducts] = useState(false)
  const bottomRef = useRef()
  const inputRef  = useRef()

  // Load shop info + deals (both public, no auth)
  useEffect(() => {
    const nameKey = `nexus_customer_name_${ownerId}`
    Promise.all([
      publicApi.get(`/shop/${ownerId}/info`),
      publicApi.get(`/shop/${ownerId}/deals`).catch(() => ({ data: { deals: [] } })),
    ]).then(([infoRes, dealsRes]) => {
      setShopInfo(infoRes.data)
      setDeals(dealsRes.data.deals || [])
      setLoading(false)
      const saved = localStorage.getItem(nameKey)
      if (saved) startChat(saved, infoRes.data, dealsRes.data.deals || [])
    }).catch(() => {
      setError('Shop not found. Please check the link.')
      setLoading(false)
    })
  }, [ownerId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  const startChat = (name, info, activeDeals) => {
    const shop = info || shopInfo
    const d = activeDeals !== undefined ? activeDeals : deals
    setCustomerName(name)
    localStorage.setItem(`nexus_customer_name_${ownerId}`, name)

    let greeting = `Hi ${name}! Welcome to ${shop?.shop_name}.\n\nAsk me anything — product availability, prices, or quantities. I'll answer from live inventory!`

    if (d.length > 0) {
      const dealNames = d.slice(0, 2).map(x => `${x.name} at Rs.${x.deal_price}/${x.unit} (${x.pct_off}% off)`).join(', ')
      greeting += `\n\nToday's deals: ${dealNames}. Ask me for details!`
    }

    setMessages([{
      role: 'bot',
      text: greeting,
      ts: Date.now(),
    }])
  }

  const changeName = () => {
    localStorage.removeItem(`nexus_customer_name_${ownerId}`)
    setCustomerName('')
    setMessages([])
    setInput('')
  }

  const sendMessage = async (text) => {
    const msg = (text || input).trim()
    if (!msg || typing) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg, ts: Date.now() }])
    setTyping(true)
    try {
      const res = await publicApi.post(`/shop/${ownerId}/chat`, {
        message: msg,
        customer_name: customerName,
      })
      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.data.reply,
        ts: Date.now(),
        intent: res.data.ml_intent,
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: 'Sorry, something went wrong. Please try again.',
        ts: Date.now(),
      }])
    } finally {
      setTyping(false)
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  // ── States ───────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="text-center">
          <div className="w-10 h-10 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Loading shop...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100 px-4">
        <div className="bg-white rounded-2xl shadow p-8 max-w-sm w-full text-center">
          <p className="text-4xl mb-3">🏪</p>
          <p className="text-gray-700 font-semibold">{error}</p>
          <p className="text-gray-400 text-xs mt-2">Check that the shop link is correct.</p>
        </div>
      </div>
    )
  }

  if (!customerName) {
    return (
      <NameEntry
        shopName={shopInfo?.shop_name}
        deals={deals}
        onSubmit={name => startChat(name, shopInfo, deals)}
      />
    )
  }

  // Quick-ask chips from live inventory
  const productChips = (shopInfo?.products || []).slice(0, 6).map(p => `Price of ${p.name}?`)

  return (
    <div className="flex flex-col h-screen max-w-lg mx-auto shadow-xl bg-gray-100">

      {/* ── Header ── */}
      <div className="bg-green-700 text-white px-4 py-3 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center font-bold text-lg shrink-0">
          {shopInfo?.shop_name?.[0] || 'S'}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm truncate">{shopInfo?.shop_name}</p>
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-green-300 rounded-full animate-pulse" />
            <p className="text-xs text-green-200">Online · AI Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* Change name — lets another customer use the same device */}
          <button
            onClick={changeName}
            title="Different customer? Change name"
            className="flex items-center gap-1 text-xs text-green-200 hover:text-white transition-colors px-2 py-1 rounded-lg hover:bg-green-600"
          >
            <Edit2 size={11} />
            <span className="hidden sm:inline">{customerName}</span>
          </button>
          <button
            onClick={() => setShowProducts(p => !p)}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
              showProducts ? 'bg-white text-green-700' : 'bg-green-600 text-white hover:bg-green-500'
            }`}
          >
            Products
          </button>
        </div>
      </div>

      {/* ── Products panel ── */}
      {showProducts && (
        <div className="bg-white border-b border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs font-semibold text-gray-600">Available Now</p>
            <button onClick={() => setShowProducts(false)}><X size={14} className="text-gray-400" /></button>
          </div>
          <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
            {shopInfo?.products?.length === 0 ? (
              <p className="text-xs text-gray-400">No products listed yet.</p>
            ) : shopInfo?.products?.map(p => (
              <button key={p.name}
                onClick={() => { sendMessage(`What is the price of ${p.name}?`); setShowProducts(false) }}
                className="text-xs bg-green-50 border border-green-200 text-green-700 rounded-full px-2.5 py-1 hover:bg-green-100 transition-colors"
              >
                {p.name} — Rs.{p.price}/{p.unit}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Chat area ── */}
      <div
        className="flex-1 overflow-y-auto px-4 pt-4 pb-2"
        style={{ background: 'repeating-linear-gradient(45deg,#e5ddd5 0,#e5ddd5 2px,#d9d0c8 2px,#d9d0c8 4px)' }}
      >
        {/* Date label */}
        <div className="flex justify-center mb-3">
          <span className="bg-white/70 text-gray-500 text-xs px-3 py-1 rounded-full shadow-sm">
            Today · {shopInfo?.shop_name}
          </span>
        </div>

        {/* Deals banner — right inside the chat, before messages */}
        <DealsBanner deals={deals} onAsk={sendMessage} />

        {messages.map((msg, i) =>
          msg.role === 'user'
            ? <UserMessage key={i} msg={msg} />
            : <BotMessage key={i} msg={msg} shopName={shopInfo?.shop_name} />
        )}
        {typing && <TypingIndicator shopName={shopInfo?.shop_name} />}
        <div ref={bottomRef} />
      </div>

      {/* ── Quick-ask chips ── */}
      <div className="bg-white border-t border-gray-200 px-3 pt-2 pb-1">
        <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
          <button onClick={() => sendMessage('What do you have in stock?')} disabled={typing}
            className="whitespace-nowrap text-xs bg-green-50 border border-green-200 text-green-700 rounded-full px-3 py-1.5 hover:bg-green-100 shrink-0 disabled:opacity-40">
            What do you have?
          </button>
          {deals.length > 0 && (
            <button onClick={() => sendMessage('What are today\'s deals and offers?')} disabled={typing}
              className="whitespace-nowrap text-xs bg-orange-50 border border-orange-200 text-orange-700 rounded-full px-3 py-1.5 hover:bg-orange-100 shrink-0 disabled:opacity-40 flex items-center gap-1">
              <Tag size={10} /> Today's deals
            </button>
          )}
          {productChips.map(q => (
            <button key={q} onClick={() => sendMessage(q)} disabled={typing}
              className="whitespace-nowrap text-xs bg-green-50 border border-green-200 text-green-700 rounded-full px-3 py-1.5 hover:bg-green-100 shrink-0 disabled:opacity-40">
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* ── Input area ── */}
      <div className="bg-white border-t border-gray-100 px-3 py-3 flex items-end gap-2">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
          placeholder="Ask about products, prices..."
          disabled={typing}
          className="flex-1 bg-gray-100 rounded-2xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-60"
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || typing}
          className="w-10 h-10 bg-green-600 text-white rounded-full flex items-center justify-center hover:bg-green-700 disabled:opacity-40 transition-colors shrink-0"
        >
          <Send size={16} />
        </button>
      </div>

      {/* ── Footer ── */}
      <div className="bg-white border-t border-gray-100 text-center py-1.5">
        <p className="text-[10px] text-gray-400">Powered by Nexus-SMB AI · Chatting as <strong>{customerName}</strong> · <button onClick={changeName} className="text-green-600 underline">Not you?</button></p>
      </div>
    </div>
  )
}
