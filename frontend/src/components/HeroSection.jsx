import { ArrowDown, ArrowRight, Leaf, ShieldCheck } from 'lucide-react'
import { useEffect, useRef } from 'react'
import ImageWithFallback from './ImageWithFallback'

export default function HeroSection({ onShopNow }) {
  const visualRef = useRef(null)

  useEffect(() => {
    const visual = visualRef.current
    if (!visual || window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.matchMedia('(max-width: 700px)').matches) return undefined
    const move = (event) => {
      const bounds = visual.getBoundingClientRect()
      const x = ((event.clientX - bounds.left) / bounds.width - .5) * 10
      const y = ((event.clientY - bounds.top) / bounds.height - .5) * 8
      visual.style.setProperty('--hero-parallax-x', `${x.toFixed(2)}px`)
      visual.style.setProperty('--hero-parallax-y', `${y.toFixed(2)}px`)
    }
    const reset = () => {
      visual.style.setProperty('--hero-parallax-x', '0px')
      visual.style.setProperty('--hero-parallax-y', '0px')
    }
    visual.addEventListener('pointermove', move)
    visual.addEventListener('pointerleave', reset)
    return () => { visual.removeEventListener('pointermove', move); visual.removeEventListener('pointerleave', reset) }
  }, [])

  return (
    <section className="hero-section page-shell" aria-labelledby="hero-title">
      <div className="hero-copy">
        <div className="eyebrow"><Leaf size={15} aria-hidden="true" /> FRESHNESS, THE WAY IT SHOULD BE</div>
        <h1 id="hero-title"><span>Fresh Choices,</span> <span>Delivered to</span> <em>Your Doorstep</em></h1>
        <p>Thoughtfully sourced produce, pantry favourites and everyday goodness — picked with care and brought to you.</p>
        <div className="hero-actions">
          <button className="button button-primary" type="button" onClick={onShopNow}>
            Shop fresh picks <ArrowRight size={17} aria-hidden="true" />
          </button>
          <a className="button button-quiet" href="#categories">
            Explore categories <ArrowDown size={16} aria-hidden="true" />
          </a>
        </div>
        <div className="hero-assurance">
          <span><ShieldCheck size={17} aria-hidden="true" /> Quality checked</span>
          <span className="assurance-divider" aria-hidden="true" />
          <span>Fresh to your doorstep</span>
        </div>
      </div>
      <div className="hero-visual" ref={visualRef}>
        <div className="hero-image-parallax">
          <ImageWithFallback
            className="hero-image"
            src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1200&q=88"
            alt="A colourful market display of fresh vegetables"
            loading="eager"
          />
        </div>
        <div className="hero-floating-note">
          <span className="note-dot" />
          <span><strong>Picked with care</strong><small>Good food starts here</small></span>
        </div>
        <div className="hero-floating-badge hero-floating-badge-top"><Leaf size={14} /> Season&apos;s best</div>
        <div className="hero-floating-badge hero-floating-badge-bottom">100% <span>goodness</span></div>
        <span className="hero-image-caption">A little closer to nature.</span>
      </div>
      <div className="hero-index" aria-hidden="true">01 <span /> 03</div>
    </section>
  )
}
