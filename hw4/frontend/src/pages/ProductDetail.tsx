import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import { styleNo, swatch } from '../catalog'
import { useStore } from '../store'

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const { catalogue, setChatOpen } = useStore()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setProduct(null)
    setError('')
    fetchProduct(productId).then(setProduct).catch((e: Error) => setError(e.message))
  }, [productId])

  if (error) return <p className="error">Product not found. <Link to="/products">Back to the catalogue</Link></p>
  if (!product) return <p className="loading">Fetching it from the stockroom…</p>

  const total = product.total_stock ?? 0

  return (
    <>
      <Link to="/products" className="back">← The Catalogue</Link>
      <article className="detail">
        <figure className="detail-figure">
          <div className="detail-mat">
            <img src={product.image_url} alt={product.name} />
          </div>
          <figcaption>{styleNo(product.product_id, catalogue)} — {product.name}, as photographed for the catalogue.</figcaption>
        </figure>
        <div className="detail-info">
          <p className="kicker">{styleNo(product.product_id, catalogue)} · {product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-desc">{product.description}</p>

          <h3 className="ledger-title">Colors</h3>
          <ul className="swatches">
            {product.colors?.map((c) => (
              <li key={c}><span className="swatch" style={{ background: swatch(c) }} />{c}</li>
            ))}
          </ul>

          <h3 className="ledger-title">On hand, by size</h3>
          <ul className="ledger">
            {product.inventory?.map((s) => (
              <li key={s.size} className={s.quantity === 0 ? 'sold-out' : ''}>
                <span className="ledger-size">{s.size}</span>
                <span className="ledger-dots" />
                <span className="ledger-qty">{s.quantity === 0 ? <em className="stamp">Sold out</em> : `${s.quantity} on hand`}</span>
              </li>
            ))}
          </ul>
          <p className="muted">{total} pieces on the shelf in all sizes.</p>

          <button className="button" onClick={() => setChatOpen(true)}>Ask about this item</button>
          <p className="muted small">The clerk knows which item you're looking at; just ask "is this in my size?"</p>
        </div>
      </article>
    </>
  )
}
