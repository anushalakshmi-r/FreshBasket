import { Leaf } from 'lucide-react'

const particles = [
  { type: 'orb', className: 'atmosphere-orb atmosphere-orb-one' },
  { type: 'orb', className: 'atmosphere-orb atmosphere-orb-two' },
  { type: 'orb', className: 'atmosphere-orb atmosphere-orb-three' },
  { type: 'leaf', className: 'atmosphere-leaf atmosphere-leaf-one' },
  { type: 'leaf', className: 'atmosphere-leaf atmosphere-leaf-two' },
  { type: 'leaf', className: 'atmosphere-leaf atmosphere-leaf-three' },
  { type: 'dot', className: 'atmosphere-dot atmosphere-dot-one' },
  { type: 'dot', className: 'atmosphere-dot atmosphere-dot-two' },
  { type: 'dot', className: 'atmosphere-dot atmosphere-dot-three' },
]

export default function FloatingAtmosphere() {
  return (
    <div className="floating-atmosphere" aria-hidden="true">
      <div className="atmosphere-glow" />
      {particles.map((particle) => (
        <span className={particle.className} key={particle.className}>
          {particle.type === 'leaf' && <Leaf size={18} strokeWidth={1.4} />}
        </span>
      ))}
    </div>
  )
}
