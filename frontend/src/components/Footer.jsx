import { ArrowUpRight, Camera, Leaf, Mail } from 'lucide-react'

const footerGroups = [
  {
    title: 'Get to know us',
    links: [
      { label: 'Our story', href: '/our-story' },
      { label: 'How we source', href: '/how-we-source' },
      { label: 'Careers', href: '/careers' },
    ],
  },
  {
    title: 'Here to help',
    links: [
      { label: 'Contact us', href: '/contact' },
      { label: 'FAQs', href: '/faqs' },
      { label: 'Delivery information', href: '/delivery-info' },
    ],
  },
  {
    title: 'The finer print',
    links: [
      { label: 'Privacy policy', href: '/privacy-policy' },
      { label: 'Terms & conditions', href: '/terms' },
      { label: 'Shopping information', href: '/shopping-info' },
    ],
  },
]

export default function Footer({ onNavigate }) {
  function handleNav(event, path) {
    event.preventDefault()
    if (onNavigate) {
      onNavigate(path)
    } else {
      const nextPath = path.replace(/\/+$/, '') || '/'
      if (window.location.pathname !== nextPath) {
        window.history.pushState({}, '', nextPath)
        window.dispatchEvent(new PopStateEvent('popstate'))
      }
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <footer className="site-footer" id="about">
      <div className="page-shell">
        <div className="footer-main">
          <div className="footer-about">
            <a
              className="brand-lockup footer-brand"
              href="/"
              onClick={(event) => handleNav(event, '/')}
              aria-label="FreshBasket home"
            >
              <span className="brand-mark"><Leaf size={21} /></span>
              <span className="brand-name">fresh<span>basket</span><small>GOOD FOOD, GOOD DAYS</small></span>
            </a>
            <p>Everyday groceries, chosen with a little more care. Good food should feel good from the very first bite.</p>
            <a
              className="footer-contact"
              href="/contact"
              onClick={(event) => handleNav(event, '/contact')}
            >
              <Mail size={16} /> hello@freshbasket.in
            </a>
          </div>
          {footerGroups.map((group) => (
            <div className="footer-links-group" key={group.title}>
              <h3>{group.title}</h3>
              {group.links.map((link) => (
                <a
                  href={link.href}
                  key={link.label}
                  onClick={(event) => handleNav(event, link.href)}
                >
                  {link.label}
                </a>
              ))}
            </div>
          ))}
          <div className="footer-social">
            <h3>Come say hello</h3>
            <a
              href="https://www.instagram.com/"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Instagram"
            >
              <Camera size={18} /> Instagram <ArrowUpRight size={14} />
            </a>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2026 FreshBasket. Made for good days.</span>
          <span>Thoughtful groceries, delivered with care.</span>
        </div>
      </div>
    </footer>
  )
}