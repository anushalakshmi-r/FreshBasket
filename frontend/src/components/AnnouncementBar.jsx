import { ArrowRight, Truck } from 'lucide-react'

export default function AnnouncementBar() {
  return (
    <div className="announcement-bar">
      <div className="announcement-inner">
        <span className="announcement-message">
          <Truck size={15} aria-hidden="true" />
          <span>Freshness at your door. Free delivery on orders over ₹499.</span>
        </span>
        <a className="announcement-link" href="#deals">
          Explore today&apos;s offers <ArrowRight size={14} aria-hidden="true" />
        </a>
      </div>
    </div>
  )
}
