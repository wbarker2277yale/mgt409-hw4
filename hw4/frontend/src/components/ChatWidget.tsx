import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { deleteChatHistory, fetchChatHistory, sendChat, type Product } from '../api'
import { useStore } from '../store'
import { Pennant } from './Ornaments'

type Message = { role: 'user' | 'assistant'; content: string; products?: Product[]; query?: string; blocked?: boolean }

// Problem 9 (F2): one-tap questions that fit the page the shopper is on.
function quickQuestions(path: string): string[] {
  if (path.startsWith('/products/')) return ['Is this in stock in my size?', 'What colors does this come in?', 'Show me similar items']
  if (path === '/products') return ['What hoodies do you have?', 'Anything under $40?', "What's in stock in XL?"]
  return ["What's good for game day?", 'Gifts under $60', 'What do you sell?']
}

export default function ChatWidget() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState('')
  const { user, chatResults, setChatResults, chatOpen: open, setChatOpen: setOpen } = useStore()
  const navigate = useNavigate()
  const location = useLocation()
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ block: 'end' }) }, [messages, thinking, open])
  useEffect(() => { if (open) inputRef.current?.focus() }, [open])

  // Problem 8: logged-in shoppers get their saved conversation back; logging out clears the panel.
  useEffect(() => {
    setMessages([])
    setError('')
    if (!user) return
    fetchChatHistory()
      .then(({ turns }) => setMessages(turns.map((t, i) => ({
        role: t.role, content: t.content, products: t.products, query: turns[i - 1]?.content,
      }))))
      .catch(() => {})
  }, [user])

  const greeting = user
    ? `Welcome back, ${user.first_name}. Ask me what we carry, what it costs, or what's in stock in your size.`
    : "Good day! I'm the clerk. Ask me what we carry, what it costs, or what's in stock in your size."

  function showProducts(products: Product[], query: string) {
    setChatResults({ query, products })
    navigate('/products')
  }

  async function ask(text: string) {
    text = text.trim()
    if (!text || thinking) return
    // Messages the content filter refused are left out, so one bad message can't block the rest.
    const history = messages.filter((m) => !m.blocked).slice(-10).map(({ role, content }) => ({ role, content }))
    const onResults = location.pathname === '/products' && chatResults
    const viewing = onResults ? chatResults.products.map((p) => p.product_id) : []
    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setError('')
    setThinking(true)
    try {
      const reply = await sendChat(text, history, location.pathname, viewing)
      setMessages((m) => {
        const next = [...m]
        if (reply.blocked) next[next.length - 1] = { ...next[next.length - 1], blocked: true }
        return [...next, { role: 'assistant', content: reply.reply, products: reply.products, query: text, blocked: reply.blocked }]
      })
      // Problem 7: search results from the agent become product cards on the Products page.
      // On a product page the shopper stays put; the reply's "Show these items" button opens them.
      if (reply.products.length > 1 && !location.pathname.startsWith('/products/')) showProducts(reply.products, text)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setThinking(false)
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    ask(input)
  }

  async function forget() {
    if (!confirm('Delete your saved chat history with Campus Customs?')) return
    await deleteChatHistory().catch(() => {})
    setMessages([])
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Shop assistant">
          <header className="chat-header">
            <div>
              <p className="chat-kicker">The Counter</p>
              <h2>Ask the Clerk</h2>
            </div>
            <button onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </header>
          <div className="chat-messages">
            <p className="chat-bubble">{greeting}</p>
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role === 'user' ? 'chat-user' : ''}`}>
                {m.content}
                {m.role === 'assistant' && m.products && m.products.length > 0 && (
                  <button className="chat-show" onClick={() => showProducts(m.products!, m.query ?? 'chat')}>
                    {m.products.length === 1 ? `See ${m.products[0].name} →` : `Show these ${m.products.length} items →`}
                  </button>
                )}
              </div>
            ))}
            {thinking && <p className="chat-bubble chat-thinking">The clerk is checking the shelves<span>.</span><span>.</span><span>.</span></p>}
            {error && <p className="chat-bubble chat-error">{error}</p>}
            <div ref={endRef} />
          </div>
          <div className="chat-chips" aria-label="Suggested questions">
            {quickQuestions(location.pathname).map((q) => (
              <button key={q} onClick={() => ask(q)} disabled={thinking}>{q}</button>
            ))}
          </div>
          <p className="chat-memory-note">
            {user
              ? <>Saved to your account. <button onClick={forget}>Delete history</button></>
              : 'Guest chat is not saved. Log in to keep your history.'}
          </p>
          <form className="chat-input" onSubmit={submit}>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. Navy crewneck in a medium?"
              aria-label="Message the clerk"
            />
            <button type="submit" disabled={thinking || !input.trim()}>Ask</button>
          </form>
        </section>
      )}
      <button className="chat-toggle" onClick={() => setOpen(!open)} aria-expanded={open}
              aria-label={open ? 'Close chat' : 'Ask the clerk'}>
        {open ? <span className="chat-close">Close ×</span> : <Pennant text="ASK THE CLERK" />}
      </button>
    </div>
  )
}
