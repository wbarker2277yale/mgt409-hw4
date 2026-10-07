import { Link, NavLink } from 'react-router-dom'
import { useStore } from '../store'
import { Crest } from './Ornaments'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, signOut } = useStore()

  return (
    <header className="masthead">
      <div className="masthead-top">
        <span>New Haven, Conn.</span>
        <span className="masthead-motto">Outfitters to the Elm City</span>
        <span>{user ? `Welcome back, ${user.first_name}` : 'Free advice at the counter'}</span>
      </div>
      <div className="masthead-main">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <Crest size={40} />
          <span className="brand-name">Campus Customs</span>
        </Link>
        <nav className="nav-links" aria-label="Main">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>{l.label}</NavLink>
          ))}
        </nav>
        <div className="nav-account">
          {user ? (
            <>
              <span className="nav-user">Hi, {user.first_name}</span>
              <button className="nav-cta" onClick={signOut}>Log out</button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log in</NavLink>
              <NavLink to="/create-account" className="nav-cta">Create account</NavLink>
            </>
          )}
        </div>
      </div>
      <div className="repp" aria-hidden="true" />
    </header>
  )
}
