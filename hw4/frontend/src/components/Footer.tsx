import { Link } from 'react-router-dom'
import { Crest } from './Ornaments'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="tartan" aria-hidden="true" />
      <div className="footer-inner">
        <Crest size={34} />
        <div>
          <p className="footer-name">Campus Customs</p>
          <p className="footer-note">Yale apparel, New Haven. An independent student shop, not an official Yale store.</p>
        </div>
        <nav className="footer-links">
          <Link to="/products">The Catalogue</Link>
          <Link to="/about">About Us</Link>
          <Link to="/login">Your Account</Link>
        </nav>
      </div>
    </footer>
  )
}
