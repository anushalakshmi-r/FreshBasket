import { ArrowRight } from 'lucide-react'
import CategoryCard from './CategoryCard'

export default function CategorySection({
  categories,
  loading,
  error,
  onRetry,
  onSelect,
}) {
  return (
    <section className="section-block categories-section page-shell" id="categories" data-reveal>
      <div className="section-heading">
        <div>
          <span className="section-kicker">A GOOD PLACE TO START</span>
          <h2>Shop by category</h2>
          <p>Find all the little things that make every day delicious.</p>
        </div>
        <a className="text-link" href="#products">Browse all products <ArrowRight size={16} /></a>
      </div>
      {loading ? (
        <p className="catalogue-message" role="status">Loading fresh categories…</p>
      ) : error ? (
        <div className="catalogue-message catalogue-error" role="alert">
          <p>{error}</p>
          <button className="button button-secondary" type="button" onClick={onRetry}>Retry categories</button>
        </div>
      ) : categories.length ? (
        <div className="category-grid">
          {categories.map((category) => (
            <CategoryCard key={category.id} category={category} onSelect={onSelect} />
          ))}
        </div>
      ) : (
        <p className="catalogue-message">No categories are available right now.</p>
      )}
    </section>
  )
}
