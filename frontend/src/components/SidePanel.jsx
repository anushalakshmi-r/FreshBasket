import { X } from 'lucide-react'
import { useEffect } from 'react'

export default function SidePanel({ open, title, onClose, children }) {
  useEffect(() => {
    if (!open) return undefined

    function handleKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="panel-layer">
      <button className="panel-backdrop" type="button" onClick={onClose} aria-label="Close panel" />
      <aside className="side-panel" role="dialog" aria-modal="true" aria-label={title}>
        <div className="panel-heading">
          <div>
            <span className="section-kicker">FRESHBASKET</span>
            <h2>{title}</h2>
          </div>
          <button className="panel-close" type="button" onClick={onClose} aria-label="Close panel">
            <X size={21} />
          </button>
        </div>
        {children}
      </aside>
    </div>
  )
}
