import { ArrowRight, Mail } from 'lucide-react'
import { useState } from 'react'

export default function Newsletter() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    if (!email.trim()) return
    setMessage('Thanks for your interest. Newsletter sign-ups will be available soon.')
    setEmail('')
  }

  return (
    <section className="newsletter-section page-shell" id="newsletter">
      <div className="newsletter-icon"><Mail size={21} aria-hidden="true" /></div>
      <div className="newsletter-copy">
        <span className="section-kicker">A FRESH NOTE, NOW AND THEN</span>
        <h2>A little goodness in your inbox.</h2>
        <p>Seasonal picks, simple ideas and the occasional lovely offer.</p>
      </div>
      <form className="newsletter-form" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="newsletter-email">Your email address</label>
        <input
          id="newsletter-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Your email address"
          required
        />
        <button type="submit" aria-label="Join the FreshBasket newsletter"><ArrowRight size={18} /></button>
        <p className="newsletter-message" aria-live="polite">{message}</p>
      </form>
    </section>
  )
}
