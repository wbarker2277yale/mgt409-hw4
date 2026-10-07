// Code-drawn ornaments (no image files): the shop crest and a felt pennant.

export function Crest({ size = 44 }: { size?: number }) {
  return (
    <svg width={size} height={size * 1.15} viewBox="0 0 80 92" aria-hidden="true" className="crest">
      <path d="M6 6h68v38c0 22-16 35-34 42C22 79 6 66 6 44z" fill="#9e1b32" stroke="#14284b" strokeWidth="4" />
      <path d="M12 12h56v32c0 18-13 29-28 35-15-6-28-17-28-35z" fill="none" stroke="#b58b3a" strokeWidth="1.5" />
      {/* an open book, after the old college arms, with a chevron of repp stripe */}
      <path d="M22 34c6-3 12-3 18 1 6-4 12-4 18-1v20c-6-3-12-3-18 1-6-4-12-4-18-1z" fill="#f2e8d0" stroke="#14284b" strokeWidth="2" />
      <path d="M40 35v20" stroke="#14284b" strokeWidth="2" />
      <path d="M26 66l14-8 14 8" fill="none" stroke="#f2e8d0" strokeWidth="3" />
    </svg>
  )
}

export function Pennant({ text, className = '' }: { text: string; className?: string }) {
  return (
    <svg viewBox="0 0 220 70" className={`pennant ${className}`} aria-hidden="true">
      <rect x="0" y="4" width="10" height="62" rx="2" fill="#14284b" />
      <path d="M10 4 L214 35 L10 66 Z" fill="#9e1b32" />
      <path d="M10 10 L196 35 L10 60" fill="none" stroke="#f2e8d0" strokeWidth="1.2" strokeDasharray="3 3" />
      <text x="20" y="39.5" fontFamily="'Libre Caslon Display', 'Big Caslon', Georgia, serif"
            fontSize={text.length > 8 ? 12.5 : 22} letterSpacing={text.length > 8 ? 1.2 : 3} fill="#f2e8d0">{text}</text>
    </svg>
  )
}
