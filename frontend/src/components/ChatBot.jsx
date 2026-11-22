import { useEffect, useRef, useState } from 'react'
import { apiUrl } from '../services/apiBase'
import './ChatBot.css'

const CHAT_ENDPOINT = apiUrl('/chat/')
const WELCOME_MESSAGE = 'Vanakkam! welcome to FreshBasket ! How can i help you ?'

export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([
    { id: 'welcome', role: 'assistant', content: WELCOME_MESSAGE },
  ])
  const [isSending, setIsSending] = useState(false)
  const messageEndRef = useRef(null)

  useEffect(() => {
    if (isOpen) messageEndRef.current?.scrollIntoView({ block: 'end' })
  }, [isOpen, messages])

  async function handleSubmit(event) {
    event.preventDefault()
    const message = input.trim()
    if (!message || isSending) return

    setInput('')
    setMessages((current) => [...current, {
      id: `${Date.now()}-user`,
      role: 'user',
      content: message,
    }])
    setIsSending(true)

    try {
      const response = await fetch(CHAT_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Unable to get a reply right now.')
      setMessages((current) => [...current, {
        id: `${Date.now()}-assistant`,
        role: 'assistant',
        content: data.reply,
      }])
    } catch (error) {
      setMessages((current) => [...current, {
        id: `${Date.now()}-error`,
        role: 'assistant',
        content: error.message || 'Unable to connect to FreshBasket right now.',
      }])
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="fresh-chatbot">
      {isOpen && (
        <section className="fresh-chatbot__window" role="dialog" aria-label="FreshBasket AI chat">
          <header className="fresh-chatbot__header">
            <strong>FreshBasket AI 🤖</strong>
            <button
              className="fresh-chatbot__close"
              type="button"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </header>
          <div className="fresh-chatbot__messages" aria-live="polite">
            {messages.map((message) => (
              <p
                className={`fresh-chatbot__message fresh-chatbot__message--${message.role}`}
                key={message.id}
              >
                {message.content}
              </p>
            ))}
            {isSending && <p className="fresh-chatbot__typing">FreshBasket AI is typing…</p>}
            <div ref={messageEndRef} />
          </div>
          <form className="fresh-chatbot__form" onSubmit={handleSubmit}>
            <input
              aria-label="Message FreshBasket AI"
              autoComplete="off"
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about a product…"
              value={input}
            />
            <button type="submit" disabled={isSending || !input.trim()}>Send</button>
          </form>
        </section>
      )}
      <button
        className="fresh-chatbot__launcher"
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        aria-label={isOpen ? 'Close FreshBasket AI chat' : 'Open FreshBasket AI chat'}
        aria-expanded={isOpen}
      >
        💬
      </button>
    </div>
  )
}
