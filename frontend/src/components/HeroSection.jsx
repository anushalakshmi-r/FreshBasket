import { ArrowDown, ArrowRight, Leaf, ShieldCheck } from 'lucide-react'
import ImageWithFallback from './ImageWithFallback'

export default function HeroSection({ onShopNow }) {
  return (
    <section className="hero-section page-shell" aria-labelledby="hero-title">
      <div className="hero-copy">
        <div className="eyebrow"><Leaf size={15} aria-hidden="true" /> FRESHNESS, THE WAY IT SHOULD BE</div>
        <h1 id="hero-title">Fresh Choices, Delivered to <em>Your Doorstep</em></h1>
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
      <div className="hero-visual">
        <ImageWithFallback
          className="hero-image"
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1200&q=88"
          alt="A colourful market display of fresh vegetables"
          loading="eager"
        />
        <div className="hero-floating-note">
          <span className="note-dot" />
          <span><strong>Picked with care</strong><small>Good food starts here</small></span>
        </div>
        <span className="hero-image-caption">A little closer to nature.</span>
      </div>
      <div className="hero-index" aria-hidden="true">01 <span /> 03</div>
    </section>
  )
}
