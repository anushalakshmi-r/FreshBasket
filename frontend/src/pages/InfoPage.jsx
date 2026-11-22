import { useState } from 'react'
import {
  ArrowLeft,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  Clock,
  HelpCircle,
  Leaf,
  Mail,
  MapPin,
  Phone,
  Send,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Truck,
} from 'lucide-react'
import { INFO_PAGE_MAP, INFO_PAGES_LIST } from '../data/infoPages'

export default function InfoPage({ slug = 'our-story', onNavigate }) {
  const [formSubmitted, setFormSubmitted] = useState(false)
  const [contactForm, setContactForm] = useState({ name: '', email: '', subject: '', message: '' })

  function handleFormSubmit(e) {
    e.preventDefault()
    setFormSubmitted(true)
  }

  function handleNavigate(path) {
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

  const normalizedSlug = INFO_PAGE_MAP[`/${slug}`] || slug

  const renderContent = () => {
    switch (normalizedSlug) {
      case 'our-story':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><Leaf size={14} /> Get to know us</span>
              <h1>Our story</h1>
              <p className="info-lead">Thoughtful groceries, chosen with care. Good food should feel good from the very first bite.</p>
            </div>
            <div className="info-prose">
              <p>
                At FreshBasket, we believe that good food is the foundation of a good day. Founded in Chennai, our journey started with a simple observation: grocery shopping in busy cities had become disconnected from the true roots of fresh produce. Vegetables spent days in trucks and storage chambers, losing the crisp flavour and vitality that makes real food nourishing.
              </p>
              <p>
                We set out to create a fresh food marketplace that bridges the gap between conscientious local farmers and households who appreciate genuine freshness. By partnering directly with trusted regional growers across Tamil Nadu and neighbouring states, we bring harvested goods straight to your doorstep without middlemen delays.
              </p>
              <div className="info-grid-3">
                <div className="info-feature-box">
                  <Leaf size={22} color="#174b35" style={{ marginBottom: 10 }} />
                  <h4>Farm-direct freshness</h4>
                  <p>Picked at peak maturity and delivered within 24 hours of harvest for unbeatable taste and nutritional goodness.</p>
                </div>
                <div className="info-feature-box">
                  <ShieldCheck size={22} color="#174b35" style={{ marginBottom: 10 }} />
                  <h4>Honest partnerships</h4>
                  <p>Fair, transparent compensation for our partner farmers and growers, supporting sustainable agricultural livelihoods.</p>
                </div>
                <div className="info-feature-box">
                  <Sparkles size={22} color="#174b35" style={{ marginBottom: 10 }} />
                  <h4>Selected with care</h4>
                  <p>Every vegetable, fruit, and pantry staple undergoes strict quality checks before it is carefully packed in your basket.</p>
                </div>
              </div>
              <h2>Our commitment to you</h2>
              <p>
                Whether you are picking up crisp greens for a family salad, seasonal mangoes, or everyday pantry essentials, our promise is always the same: food handled with care, honest pricing, and prompt delivery. We want every FreshBasket order to make your cooking simpler and your meals more memorable.
              </p>
            </div>
          </>
        )

      case 'how-we-source':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><Leaf size={14} /> From farm to kitchen</span>
              <h1>How we source</h1>
              <p className="info-lead">Carefully vetted family farms, soil-first agriculture, and cold-chain integrity from seed to doorstep.</p>
            </div>
            <div className="info-prose">
              <p>
                Great meals begin in healthy soil. That is why our sourcing process begins months before produce ever reaches our catalogue. We work directly with over 150 local farmers and artisan producers who prioritize soil enrichment, organic pest management, and natural cultivation practices.
              </p>
              <p>
                Instead of sourcing anonymously from wholesale market auctions, our agronomy team visits partner farms regularly. We test irrigation water quality and ensure crops are grown without harmful synthetic chemical pesticides.
              </p>
              <div className="info-grid-3">
                <div className="info-feature-box">
                  <h4>1. Soil & seed verification</h4>
                  <p>We work exclusively with certified cultivators who use non-GMO seeds and maintain chemical-free soil biodiversity.</p>
                </div>
                <div className="info-feature-box">
                  <h4>2. Synchronized morning harvest</h4>
                  <p>Crops are picked at dawn at optimal ripeness, locking in natural moisture, aroma, and essential vitamins.</p>
                </div>
                <div className="info-feature-box">
                  <h4>3. Gentle cold-chain logistics</h4>
                  <p>Transferred in temperature-controlled crates to our Chennai hubs, minimizing heat exposure and transit bruising.</p>
                </div>
              </div>
              <h2>Zero artificial ripening or waxes</h2>
              <p>
                Unlike commercial supermarkets, we never spray our fruits with artificial glossy waxes or use carbide ripening chambers. What you see is authentic nature: vibrant, wholesome, and ready to nourish your family.
              </p>
            </div>
          </>
        )

      case 'careers':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><Briefcase size={14} /> Join our mission</span>
              <h1>Careers at FreshBasket</h1>
              <p className="info-lead">Help us build India&apos;s most reliable, farm-connected grocery experience.</p>
            </div>
            <div className="info-prose">
              <p>
                At FreshBasket, we are a team of problem-solvers, food lovers, and engineers rethinking the modern food supply chain. Building a seamless digital experience that delivers perishable farm produce fresh every single morning requires creativity, speed, and genuine empathy for both our customers and our partner farmers.
              </p>
              <p>
                We believe in autonomous ownership, rapid iteration, and transparent collaboration. We provide competitive salaries, comprehensive health coverage, flexible working options, and generous grocery discounts.
              </p>
              <h2>Current openings</h2>
              <div className="info-grid-3">
                <div className="info-feature-box">
                  <h4>Full-Stack Engineer (React / Python)</h4>
                  <p>Engineering • Chennai / Hybrid</p>
                  <p style={{ marginTop: 8, fontSize: 13, color: '#556657' }}>Build responsive storefront features and real-time inventory management microservices.</p>
                </div>
                <div className="info-feature-box">
                  <h4>Supply Chain Operations Manager</h4>
                  <p>Operations • Chennai Hub</p>
                  <p style={{ marginTop: 8, fontSize: 13, color: '#556657' }}>Oversee regional distribution centers, morning intake routes, and cold-chain compliance.</p>
                </div>
                <div className="info-feature-box">
                  <h4>Produce Quality Specialist</h4>
                  <p>Quality Assurance • Chennai</p>
                  <p style={{ marginTop: 8, fontSize: 13, color: '#556657' }}>Conduct daily harvest quality inspections and champion grower grading standards.</p>
                </div>
              </div>
              <p>
                Interested in working with us? Send your resume and a short note about why fresh food matters to you to <strong style={{ color: 'var(--forest)' }}>careers@freshbasket.in</strong>.
              </p>
            </div>
          </>
        )

      case 'contact':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><Mail size={14} /> Here to help</span>
              <h1>Contact us</h1>
              <p className="info-lead">We would love to hear from you. Reach out with questions, feedback, or custom requests.</p>
            </div>
            <div className="info-contact-grid">
              <div className="info-contact-card">
                <h4><Mail size={18} /> Email support</h4>
                <p>For order questions, feedback, or general inquiries:</p>
                <strong>hello@freshbasket.in</strong>
                <p style={{ marginTop: 6, fontSize: 13, color: 'var(--muted)' }}>Typical response time: under 2 hours</p>
              </div>
              <div className="info-contact-card">
                <h4><Phone size={18} /> Helpline</h4>
                <p>Customer care assistance 7 days a week:</p>
                <strong>+91 98400 12345</strong>
                <p style={{ marginTop: 6, fontSize: 13, color: 'var(--muted)' }}>Available daily: 6:00 AM – 10:00 PM</p>
              </div>
              <div className="info-contact-card">
                <h4><MapPin size={18} /> Headquarters</h4>
                <p>FreshBasket Retail Private Limited</p>
                <strong>OMR IT Expressway, Chennai</strong>
                <p style={{ marginTop: 6, fontSize: 13, color: 'var(--muted)' }}>Tamil Nadu, 600096</p>
              </div>
            </div>

            <div className="info-prose">
              <h2>Send us a message</h2>
              {formSubmitted ? (
                <div className="info-feature-box" style={{ background: '#e8f5e9', borderColor: '#c8e6c9', padding: '24px 28px' }}>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green-dark)' }}>
                    <CheckCircle2 size={20} /> Thank you for reaching out!
                  </h4>
                  <p style={{ color: '#2e5b38' }}>We have received your message and our Chennai support team will get back to you shortly at {contactForm.email || 'your email'}.</p>
                </div>
              ) : (
                <form className="info-form" onSubmit={handleFormSubmit}>
                  <div className="info-form-row">
                    <label>
                      Your name
                      <input
                        type="text"
                        required
                        placeholder="e.g. Priyadarshini"
                        value={contactForm.name}
                        onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                      />
                    </label>
                    <label>
                      Your email
                      <input
                        type="email"
                        required
                        placeholder="e.g. name@example.com"
                        value={contactForm.email}
                        onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                      />
                    </label>
                  </div>
                  <label>
                    Subject
                    <input
                      type="text"
                      required
                      placeholder="e.g. Question about my delivery slot"
                      value={contactForm.subject}
                      onChange={(e) => setContactForm({ ...contactForm, subject: e.target.value })}
                    />
                  </label>
                  <label>
                    Message
                    <textarea
                      rows={5}
                      required
                      placeholder="Write your message here..."
                      value={contactForm.message}
                      onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                    />
                  </label>
                  <button type="submit" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <Send size={16} /> Send message
                  </button>
                </form>
              )}
            </div>
          </>
        )

      case 'faqs':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><HelpCircle size={14} /> Questions answered</span>
              <h1>Frequently Asked Questions</h1>
              <p className="info-lead">Quick answers to common questions about orders, deliveries, payments, and product freshness.</p>
            </div>
            <div className="info-prose">
              <div className="info-faq-item">
                <h3>How fresh is the produce I receive from FreshBasket?</h3>
                <p>
                  All our fresh vegetables and fruits are harvested daily at dawn from partner farms within 100km of our Chennai hubs. They are sorted, packed, and delivered to your doorstep within 24 hours of harvest, ensuring peak flavour, crispness, and nutrient retention.
                </p>
              </div>
              <div className="info-faq-item">
                <h3>What are your delivery slots and operational hours?</h3>
                <p>
                  We offer three scheduled delivery slots 7 days a week: Morning (6:00 AM – 9:00 AM), Midday (11:00 AM – 2:00 PM), and Evening (5:00 PM – 9:00 PM). You can choose your preferred time window during checkout.
                </p>
              </div>
              <div className="info-faq-item">
                <h3>What if I am unhappy with the quality of an item?</h3>
                <p>
                  We have a 100% No-Questions-Asked Freshness Guarantee. If an item arrives bruised, under-ripe, or not up to standard, simply let us know via your Orders page or email hello@freshbasket.in for an instant replacement or immediate wallet/original payment refund.
                </p>
              </div>
              <div className="info-faq-item">
                <h3>What is the minimum order amount for free delivery?</h3>
                <p>
                  Orders of ₹499 and above receive free delivery across all supported Chennai locations. Orders below ₹499 have a nominal delivery charge of ₹40.
                </p>
              </div>
              <div className="info-faq-item">
                <h3>What payment options do you support?</h3>
                <p>
                  We accept UPI (Google Pay, PhonePe, Paytm, BHIM), all major Credit and Debit Cards (Visa, MasterCard, RuPay), Net Banking from leading banks, and Cash / UPI on Delivery.
                </p>
              </div>
              <div className="info-faq-item">
                <h3>Can I track my delivery in real time?</h3>
                <p>
                  Yes! Once your order is dispatched from our local fulfillment center, you will receive real-time updates and can follow the delivery progress on your &quot;My orders&quot; page.
                </p>
              </div>
            </div>
          </>
        )

      case 'delivery-info':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><Truck size={14} /> At your doorstep</span>
              <h1>Delivery information</h1>
              <p className="info-lead">Reliable, prompt, and gentle delivery across Chennai, right when you need it.</p>
            </div>
            <div className="info-prose">
              <p>
                When it comes to delicate fresh greens, ripe tomatoes, and artisanal dairy, careful delivery matters just as much as quality harvesting. FreshBasket operates its own temperature-controlled local delivery network to guarantee your groceries reach your kitchen in pristine shape.
              </p>
              <h2>Daily delivery slots</h2>
              <div className="info-grid-3">
                <div className="info-feature-box">
                  <Clock size={20} color="#174b35" style={{ marginBottom: 8 }} />
                  <h4>Morning slot</h4>
                  <p><strong>6:00 AM – 9:00 AM</strong></p>
                  <p style={{ marginTop: 6, fontSize: 13, color: '#556657' }}>Ideal for morning breakfast prep, fresh herbs, and milk for the day ahead.</p>
                </div>
                <div className="info-feature-box">
                  <Clock size={20} color="#174b35" style={{ marginBottom: 8 }} />
                  <h4>Midday slot</h4>
                  <p><strong>11:00 AM – 2:00 PM</strong></p>
                  <p style={{ marginTop: 6, fontSize: 13, color: '#556657' }}>Convenient lunch-hour replenishment for household essentials and fresh snacks.</p>
                </div>
                <div className="info-feature-box">
                  <Clock size={20} color="#174b35" style={{ marginBottom: 8 }} />
                  <h4>Evening slot</h4>
                  <p><strong>5:00 PM – 9:00 PM</strong></p>
                  <p style={{ marginTop: 6, fontSize: 13, color: '#556657' }}>Arrives right on time for dinner cooking and evening family meals.</p>
                </div>
              </div>
              <h2>Service coverage areas</h2>
              <p>
                We currently deliver throughout Chennai, covering Anna Nagar, T. Nagar, Velachery, OMR, Tambaram, Porur, Adyar, Kodambakkam, Mylapore, Alwarpet, Nungambakkam, and surrounding neighbourhoods. Select your location in the top navigation bar to check immediate slot availability for your pincode.
              </p>
              <h2>Eco-conscious packaging</h2>
              <p>
                We are committed to reducing single-use plastic waste. Our groceries are delivered in biodegradable paper bags and sturdy reusable delivery totes that our delivery partner collects on your next order if you wish.
              </p>
            </div>
          </>
        )

      case 'privacy-policy':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><ShieldCheck size={14} /> Trust & safety</span>
              <h1>Privacy policy</h1>
              <p className="info-lead">Last updated: November 2026. How we collect, safeguard, and use your personal data.</p>
            </div>
            <div className="info-prose">
              <p>
                At FreshBasket, we value your trust above all else. This Privacy Policy describes how FreshBasket collects, utilizes, and protects the personal information you share with us when browsing our platform or placing grocery orders.
              </p>
              <h2>1. Information we collect</h2>
              <p>
                When you create an account, enter a delivery address, or place an order, we collect basic details including your name, delivery address, phone number, and email. For seamless payments, transactions are processed securely through RBI-compliant, PCI-DSS certified payment gateways. We never store credit or debit card numbers on our servers.
              </p>
              <h2>2. How we use your data</h2>
              <p>
                Your personal details are used exclusively to process your grocery orders, coordinate timely deliveries, send status notifications, and communicate important service updates. We do not sell, rent, or trade your personal information to third-party advertisers.
              </p>
              <h2>3. Account security & encryption</h2>
              <p>
                We employ industry-standard TLS 1.3 encryption protocols for all network communications. Your account credentials and session tokens are safeguarded using cryptographic hashing and strict server-side access controls.
              </p>
              <h2>4. Your privacy rights</h2>
              <p>
                You have the full right to view, modify, or permanently request deletion of your account and personal data at any time. To exercise these rights or request a copy of your stored records, please email our privacy team at <strong style={{ color: 'var(--forest)' }}>privacy@freshbasket.in</strong>.
              </p>
            </div>
          </>
        )

      case 'terms':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><Leaf size={14} /> The finer print</span>
              <h1>Terms &amp; conditions</h1>
              <p className="info-lead">Last updated: November 2026. Terms governing the use of FreshBasket services and orders.</p>
            </div>
            <div className="info-prose">
              <p>
                Welcome to FreshBasket. By accessing our website, creating an account, or placing an order, you agree to be bound by these Terms and Conditions. Please review them carefully before making a purchase.
              </p>
              <h2>1. Account responsibilities</h2>
              <p>
                You are responsible for maintaining the confidentiality of your account credentials and password. You agree to provide accurate and complete contact and delivery information when placing orders. FreshBasket reserves the right to suspend accounts with fraudulent or abusive activity.
              </p>
              <h2>2. Product pricing & availability</h2>
              <p>
                Because our fresh produce is harvested daily based on seasonal agricultural yields, certain items may occasionally become unavailable due to dawn weather conditions. In such instances, we promptly notify you and process an instant refund for the affected items. All displayed prices are in Indian Rupees (INR) and are inclusive of applicable taxes.
              </p>
              <h2>3. Order cancellations & refunds</h2>
              <p>
                Orders may be cancelled free of charge at any time prior to packaging and dispatch. If you receive an item that fails to meet our quality standards, you are eligible for an immediate replacement or full refund under our 100% Freshness Guarantee.
              </p>
              <h2>4. Limitation of liability</h2>
              <p>
                FreshBasket aims to maintain continuous uptime and timely delivery. However, we are not liable for transit delays caused by force majeure events, severe weather disruptions, or civic road restrictions.
              </p>
            </div>
          </>
        )

      case 'shopping-info':
        return (
          <>
            <div className="info-header">
              <span className="info-eyebrow"><ShoppingBag size={14} /> Seamless shopping</span>
              <h1>Shopping information</h1>
              <p className="info-lead">A helpful guide to navigating categories, placing orders, and saving on your weekly basket.</p>
            </div>
            <div className="info-prose">
              <p>
                Shopping at FreshBasket is designed to be effortless, transparent, and enjoyable. Here is everything you need to know to make the most of our grocery store:
              </p>
              <div className="info-grid-3">
                <div className="info-feature-box">
                  <h4>1. Browse &amp; search</h4>
                  <p>Explore our curated categories—from farm-fresh vegetables and fruits to dairy and pantry staples—or use the search bar for instant recommendations.</p>
                </div>
                <div className="info-feature-box">
                  <h4>2. Basket &amp; wishlist</h4>
                  <p>Click &quot;Add to basket&quot; for instant items, or tap the heart icon on any card to save seasonal favourites to your personal wishlist.</p>
                </div>
                <div className="info-feature-box">
                  <h4>3. Choose your slot</h4>
                  <p>Select your delivery neighbourhood and pick the morning, afternoon, or evening time slot that best fits your daily cooking routine.</p>
                </div>
              </div>
              <h2>Helpful shopping tips</h2>
              <div className="info-faq-item">
                <h3>Today&apos;s deals &amp; seasonal specials</h3>
                <p>Check the &quot;Today&apos;s deals&quot; section on the home page every morning for special discounts on harvest overruns and seasonal fruit batches.</p>
              </div>
              <div className="info-faq-item">
                <h3>Repeat ordering made simple</h3>
                <p>Visit your &quot;My orders&quot; page at any time to view past purchases and re-order your regular household staples with a single click.</p>
              </div>
              <div className="info-faq-item">
                <h3>Easy order tracking</h3>
                <p>Track your delivery rider in real time and receive SMS notifications when your basket is safely delivered at your doorstep.</p>
              </div>
            </div>
          </>
        )

      default:
        return (
          <div className="info-prose">
            <div className="info-header">
              <h1>Information</h1>
              <p className="info-lead">Explore information about FreshBasket below.</p>
            </div>
            <p>Please select a topic from the sidebar to view full details.</p>
          </div>
        )
    }
  }

  const currentTopic = INFO_PAGES_LIST.find((item) => item.slug === normalizedSlug) || INFO_PAGES_LIST[0]

  return (
    <div className="info-page-wrap">
      <div className="info-page-shell">
        <nav className="info-breadcrumbs" aria-label="Breadcrumb">
          <button type="button" onClick={() => handleNavigate('/')}>Home</button>
          <span>/</span>
          <span>{currentTopic.label}</span>
        </nav>

        <div className="info-layout">
          <aside className="info-sidebar" aria-label="Information topics">
            <span className="info-sidebar-title">Information</span>
            {INFO_PAGES_LIST.map((page) => (
              <button
                type="button"
                key={page.slug}
                className={`info-sidebar-link${page.slug === normalizedSlug ? ' is-active' : ''}`}
                onClick={() => handleNavigate(page.href)}
              >
                <span>{page.label}</span>
                <ChevronRight size={15} />
              </button>
            ))}
          </aside>

          <main className="info-content-card">
            {renderContent()}

            <div className="info-cta-bar">
              <button
                type="button"
                className="info-back-button"
                onClick={() => handleNavigate('/')}
              >
                <ArrowLeft size={16} /> Continue shopping
              </button>
              <span style={{ fontSize: 13, color: 'var(--muted)' }}>
                Fresh groceries delivered daily across Chennai.
              </span>
            </div>
          </main>
        </div>
      </div>
    </div>
  )
}
