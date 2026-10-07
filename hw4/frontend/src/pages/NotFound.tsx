import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="about">
      <p className="kicker">Error 404</p>
      <h1>That page has gone to the Game.</h1>
      <Link to="/" className="button">Back to home</Link>
    </section>
  )
}
