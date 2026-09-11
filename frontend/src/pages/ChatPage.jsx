import { useState, useEffect, useRef } from 'react'
import api from '../api/client'
import { Send, Mic, MicOff, Trash2, Bot, CheckCircle, RefreshCw, Activity, ChevronDown, ChevronUp, ShieldCheck, Database, HelpCircle } from 'lucide-react'

const QUICK_PROMPTS = [
  'How am I doing today?',
  'Which items are not selling?',
  'What should I restock urgently?',
  'Calculate my profit margin',
  'Give me a discount strategy',
  'What is my best selling item?',
]

function TraceBadge({ trace }) {
  const [open, setOpen] = useState(false)
  if (!trace) return null

  return (
    <div className="mt-2 text-xs border border-indigo-100 bg-indigo-50/70 rounded-xl overflow-hidden shadow-xs">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-1.5 text-indigo-700 hover:bg-indigo-100/50 transition-colors font-medium">
        <div className="flex items-center gap-1.5">
          <Activity size={13} className="text-indigo-600 animate-pulse" />
          <span>Agent Trace: <strong className="font-semibold">{trace.intent}</strong></span>
          {trace.grounded_source && (
            <span className="bg-emerald-100 text-emerald-700 px-1.5 py-0.2 rounded text-[10px] font-semibold flex items-center gap-0.5">
              <Database size={9} /> SQLite Grounded
            </span>
          )}
          {trace.verification && (
            <span className="bg-blue-100 text-blue-700 px-1.5 py-0.2 rounded text-[10px] font-semibold flex items-center gap-0.5">
              <ShieldCheck size={9} /> Verified
            </span>
          )}
        </div>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {open && (
        <div className="p-3 bg-white border-t border-indigo-100 space-y-2 text-gray-700 font-mono text-[11px]">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-gray-400 block text-[10px] uppercase font-sans">Intent (Session 1)</span>
              <span className="font-semibold text-gray-900">{trace.intent}</span>
            </div>
            <div>
              <span className="text-gray-400 block text-[10px] uppercase font-sans">Confidence</span>
              <span>{Math.round((trace.confidence || 1) * 100)}%</span>
            </div>
          </div>

          <div>
            <span className="text-gray-400 block text-[10px] uppercase font-sans">Entities Extracted</span>
            <pre className="bg-gray-50 p-1.5 rounded border border-gray-100 text-[10px] overflow-x-auto">
              {JSON.stringify(trace.entities || {}, null, 2)}
            </pre>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 border-t border-gray-100">
            <div>
              <span className="text-gray-400 block text-[10px] uppercase font-sans">Tool Executed (Session 2)</span>
              <span className="text-blue-600 font-medium">{trace.tool_executed || 'None (Read-only)'}</span>
            </div>
            <div>
              <span className="text-gray-400 block text-[10px] uppercase font-sans">Safety Gate / Approval</span>
              <span className="text-emerald-600 font-medium">
                {String(trace.verification || 'Passed Safe')}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ActionBadge({ action }) {
  if (!action || action.error) return null
  const labels = {
    price_update: `✅ Price updated: ${action.item} → sell ₹${action.selling_price ?? ''}${action.cost_price ? ` cost ₹${action.cost_price}` : ''}`,
    purchase:     `✅ Stock added for ${action.items_updated} item(s)`,
    sale:         `✅ Sale recorded for ${action.items_recorded} item(s)`,
    expense:      `✅ Expense ₹${action.amount} recorded`,
  }
  const text = labels[action.type]
  if (!text) return null
  return (
    <div className="flex items-center gap-1.5 mt-2 text-xs text-green-700 bg-green-50 border border-green-200 rounded-full px-3 py-1 w-fit">
      <CheckCircle size={12} />
      {text}
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages]     = useState([])   // {role, content, timestamp, action_taken?}
  const [input, setInput]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [listening, setListening]   = useState(false)
  const [historyLoading, setHistoryLoading] = useState(true)
  const bottomRef    = useRef(null)
  const recognitionRef = useRef(null)
  const inputRef     = useRef(null)

  // Load history from DB every time this page is visited
  const loadHistory = () => {
    setHistoryLoading(true)
    api.get('/chat/history')
      .then(res => {
        // Map DB format to local format
        setMessages((res.data || []).map(m => ({
          role:      m.role,
          content:   m.content,
          timestamp: m.timestamp || new Date().toISOString(),
        })))
      })
      .catch(() => setMessages([]))
      .finally(() => setHistoryLoading(false))
  }

  useEffect(() => {
    loadHistory()
    // Re-load when tab becomes visible again (user switches back)
    const onVisible = () => { if (document.visibilityState === 'visible') loadHistory() }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text) => {
    const msg = text || input
    if (!msg.trim() || loading) return
    setInput('')

    // Add user message locally immediately
    const userMsg = { role: 'user', content: msg, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await api.post('/chat/message', { message: msg })
      const aiMsg = {
        role: 'assistant',
        content: res.data.response,
        timestamp: new Date().toISOString(),
        action_taken: res.data.action_taken || null,
        trace: res.data.trace || null,
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (e) {
      const errDetail = e.response?.data?.detail || e.message || 'Unknown error'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, something went wrong: ${errDetail}`,
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const startVoice = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Voice input not supported. Use Chrome browser.')
      return
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SR()
    recognition.lang = 'en-IN'
    recognition.interimResults = false
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript
      setInput(transcript)
      setListening(false)
    }
    recognition.onerror = () => setListening(false)
    recognition.onend  = () => setListening(false)
    recognition.start()
    recognitionRef.current = recognition
    setListening(true)
  }

  const stopVoice = () => { recognitionRef.current?.stop(); setListening(false) }

  const clearHistory = async () => {
    if (!confirm('Clear all chat history?')) return
    await api.delete('/chat/history')
    setMessages([])
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center shadow">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900">AI Business Assistant</h1>
            <p className="text-xs text-gray-400">Powered by Gemini · knows your shop, saves everything to DB</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={loadHistory} title="Reload history"
            className="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-lg transition-colors">
            <RefreshCw size={16} />
          </button>
          <button onClick={clearHistory} title="Clear history"
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Persistent memory notice */}
      <div className="bg-blue-50 border-b border-blue-100 px-5 py-2 text-xs text-blue-700 flex items-center gap-2">
        <span className="w-2 h-2 bg-blue-400 rounded-full shrink-0" />
        Chat history is saved permanently — switching tabs or refreshing won't erase it.
        Context is loaded fresh with each message.
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">

        {historyLoading && (
          <p className="text-gray-400 text-sm text-center py-8">Loading your conversation history...</p>
        )}

        {!historyLoading && messages.length === 0 && (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Bot size={32} className="text-blue-500" />
            </div>
            <h3 className="font-bold text-gray-800 mb-2 text-lg">Your AI Business Advisor</h3>
            <p className="text-gray-400 text-sm mb-2">Ask anything about your shop. I can also update your records.</p>
            <p className="text-gray-300 text-xs mb-8">
              Try: "change milk sell price to ₹32" or "bought 20 sugar at ₹45"
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {QUICK_PROMPTS.map(p => (
                <button key={p} onClick={() => sendMessage(p)}
                  className="bg-blue-50 text-blue-700 text-sm px-4 py-2 rounded-full hover:bg-blue-100 transition-colors border border-blue-100">
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'user' ? (
              <div className="max-w-[75%]">
                <div className="bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-sm">
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                </div>
                <p className="text-right text-xs text-gray-300 mt-1">
                  {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            ) : (
              <div className="max-w-[78%]">
                <div className="flex items-start gap-2">
                  <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                    <Bot size={14} className="text-white" />
                  </div>
                  <div>
                    <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100">
                      <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {/* Show action badge if this message triggered a DB update */}
                    <ActionBadge action={msg.action_taken} />
                    {/* Course presentation: Expose the developer trace (Intent, Grounding, Tools, Verification) */}
                    <TraceBadge trace={msg.trace} />
                    <p className="text-xs text-gray-300 mt-1 ml-1">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg flex items-center justify-center shrink-0">
                <Bot size={14} className="text-white" />
              </div>
              <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-gray-100">
                <div className="flex gap-1 items-center h-4">
                  {[0, 150, 300].map(d => (
                    <div key={d} className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
                      style={{ animationDelay: `${d}ms` }} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      {messages.length > 0 && (
        <div className="px-4 pb-2 flex gap-2 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
          {QUICK_PROMPTS.map(p => (
            <button key={p} onClick={() => sendMessage(p)} disabled={loading}
              className="flex-shrink-0 text-xs bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-full hover:bg-gray-50 transition-colors disabled:opacity-40">
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              className="input resize-none py-3 text-sm"
              rows={2}
              placeholder={`Ask anything or record data:\n"change milk sell price to ₹32" · "bought 20 sugar at ₹45" · "how am I doing?"`}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) }
              }}
            />
          </div>
          <button onClick={listening ? stopVoice : startVoice}
            className={`p-3 rounded-xl transition-all shrink-0 ${
              listening ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`} title="Voice input">
            {listening ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          <button onClick={() => sendMessage(input)} disabled={!input.trim() || loading}
            className="btn-primary p-3 rounded-xl shrink-0 disabled:opacity-40">
            <Send size={18} />
          </button>
        </div>
        <p className="text-xs text-gray-300 mt-2 text-center">
          Enter to send · Shift+Enter new line · 🎙 for voice
        </p>
      </div>
    </div>
  )
}
