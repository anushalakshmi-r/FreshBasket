import { ArrowRight, Leaf, Sparkles, Truck } from 'lucide-react'

const messages = [
  'Freshness at your door. Free delivery on orders over ₹499.',
  'Fresh products delivered to your doorstep.',
  'Quality and freshness, guaranteed.',
  'Shop fresh, live fresh.',
]

export default function AnnouncementBar() {
  return (
    <div className="announcement-bar" role="status">
      <div className="announcement-inner">
        <div className="announcement-marquee" aria-label="FreshBasket updates">
          <div className="announcement-track">
            {[...messages, ...messages].map((message, index) => (
              <span className="announcement-message" key={`${message}-${index}`}>
                {index % 3 === 0 ? <Truck size={15} aria-hidden="true" /> : index % 3 === 1 ? <Leaf size={15} aria-hidden="true" /> : <Sparkles size={15} aria-hidden="true" />}
                <span>{message}</span><i aria-hidden="true">✦</i>
              </span>
            ))}
          </div>
        </div>
        <a className="announcement-link" href="#deals">
          Explore today&apos;s offers <ArrowRight size={14} aria-hidden="true" />
        </a>
      </div>
    </div>
  )
}
