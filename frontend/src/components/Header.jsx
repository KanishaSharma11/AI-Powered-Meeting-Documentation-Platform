export function Header() {
  return (
    <header className="flex flex-wrap items-baseline justify-between gap-5 border-b border-rule px-10 py-7">
      <div>
        <h1 className="font-display text-[26px] font-bold tracking-tight text-ink">
          Evidence Desk
        </h1>
        <div className="mt-1 font-mono text-[11px] uppercase tracking-wider text-ink-soft">
          AI Meeting Documentation — Stage 1 &amp; 2
        </div>
      </div>
      <div className="rounded-sm border border-sage px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-sage">
        Every claim, sourced
      </div>
    </header>
  );
}   