import { ArrowRight } from 'lucide-react'
import ImageWithFallback from './ImageWithFallback'

export default function PromoBanner({ banner, onAction }) {
  return (
    <article className={`promo-card ${banner.theme}`}>
      <ImageWithFallback className="promo-image" src={banner.image} alt="" />
      <div className="promo-copy">
        <span className="promo-kicker">{banner.kicker}</span>
        <h3>{banner.title}</h3>
        <p>{banner.description}</p>
        <button className="promo-link" type="button" onClick={() => onAction(banner.target)}>
          {banner.action} <ArrowRight size={15} />
        </button>
      </div>
    </article>
  )
}
