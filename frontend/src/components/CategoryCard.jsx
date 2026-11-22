import { ArrowUpRight } from 'lucide-react'
import ImageWithFallback from './ImageWithFallback'

export default function CategoryCard({ category, onSelect }) {
  return (
    <button
      className="category-card"
      type="button"
      onClick={() => onSelect(category)}
      aria-label={`Browse ${category.name}`}
    >
      <ImageWithFallback
        className="category-image"
        src={category.image}
        alt=""
      />
      <span className="category-name">{category.name}</span>
      <span className="category-arrow" aria-hidden="true"><ArrowUpRight size={15} /></span>
    </button>
  )
}
