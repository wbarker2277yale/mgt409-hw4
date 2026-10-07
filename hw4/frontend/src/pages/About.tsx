import { Link } from 'react-router-dom'
import { Crest } from '../components/Ornaments'

export default function About() {
  return (
    <section className="about">
      <Crest size={64} />
      <p className="kicker">About Us</p>
      <h1>A small shop for the long walk across campus.</h1>
      <div className="about-columns">
        <p>
          Campus Customs is a student shop for Yale apparel: T-shirts, hoodies, crewnecks, quarter-zips,
          and jackets for game days, team pride, and the everyday walk to class. Our catalogue takes its
          manners from the old New Haven outfitters on York Street and from the campus snapshots of the
          1960s: navy and white, sensible cloth, and nothing louder than it needs to be.
        </p>
        <p>
          Not sure of a size? The clerk in the corner checks the real stock on every shelf, size by size,
          and will tell you plainly when something is sold out. We're an independent student shop, not an
          official Yale store.
        </p>
      </div>
      <Link to="/products" className="button">Browse the Catalogue</Link>
    </section>
  )
}
