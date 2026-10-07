import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { CATEGORIES, categoryOf } from '../catalog'
import ProductCard from '../components/ProductCard'
import { Pennant } from '../components/Ornaments'
import { useStore } from '../store'

// Three snapshots for the cover, captioned like a 1965 campus photo book.
const COVER = [
  { id: 'basic-hoodie-big-yale', caption: 'Fig. 1 — The big YALE hoodie, Cross Campus, 8:50 a.m.' },
  { id: 'baseball-left-chest-crewneck', caption: 'Fig. 2 — Crewneck, between innings' },
  { id: '2025-yale-vs-harvard-t-shirt', caption: 'Fig. 3 — Dressed for The Game' },
]

export default function Home() {
  const { catalogue, setChatOpen } = useStore()
  const cover = COVER.map((c) => ({ ...c, product: catalogue.find((p) => p.product_id === c.id) }))
  const featured = catalogue.filter((p) => !COVER.some((c) => c.id === p.product_id)).filter((_, i) => i % 9 === 4).slice(0, 4)

  return (
    <>
      <section className="cover">
        <div className="cover-text">
          <p className="kicker">The Fall Catalogue · Vol. IV</p>
          <h1>Dressed<br />for the <em>Quad.</em></h1>
          <p className="cover-lede">
            Hoodies, crewnecks, tees, and quarter-zips in the old Ivy manner: navy and white, sensible,
            built for the walk to class and the Saturday after.
          </p>
          <div className="cover-actions">
            <Link to="/products" className="button">Browse the Catalogue</Link>
            <button className="button button-ghost" onClick={() => setChatOpen(true)}>Ask the Clerk</button>
          </div>
        </div>
        <div className="snapshots" aria-label="Featured products">
          {cover.map((c, i) => c.product && (
            <Link key={c.id} to={`/products/${c.id}`} className={`snapshot snapshot-${i + 1}`}>
              <img src={c.product.image_url} alt={c.product.name} />
              <span className="snapshot-caption">{c.caption}</span>
            </Link>
          ))}
          <Pennant text="CAMPUS" className="cover-pennant" />
        </div>
      </section>

      <section className="departments">
        <h2 className="section-title"><span>The Departments</span></h2>
        <div className="dept-grid">
          {CATEGORIES.map((c, i) => {
            const items = catalogue.filter((p) => categoryOf(p) === c.key)
            const low = items.length ? Math.min(...items.map((p) => p.price)) : 0
            return (
              <Link key={c.key} to={`/products?cat=${c.key}`} className="dept">
                <span className="dept-no">{['I', 'II', 'III', 'IV', 'V'][i]}</span>
                <span className="dept-name">{c.label}</span>
                <span className="dept-blurb">{c.blurb}</span>
                <span className="dept-meta">{items.length} styles{items.length ? ` · from ${formatPrice(low)}` : ''}</span>
              </Link>
            )
          })}
        </div>
      </section>

      {featured.length > 0 && (
        <section>
          <h2 className="section-title"><span>On the Shelf This Week</span></h2>
          <div className="grid">
            {featured.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} />)}
          </div>
        </section>
      )}
    </>
  )
}
