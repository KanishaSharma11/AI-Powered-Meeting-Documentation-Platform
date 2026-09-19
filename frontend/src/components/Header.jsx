import { useAuth } from '../lib/auth';

const TABS = [
  { id: 'meetings', label: 'Meetings' },
  { id: 'projects', label: 'Projects' },
  { id: 'templates', label: 'Templates' },
];

function SealMark() {
  return (
    <svg viewBox="0 0 32 32" className="h-8 w-8 shrink-0" aria-hidden="true">
      <circle cx="16" cy="16" r="14.5" fill="none" stroke="var(--color-ink)" strokeWidth="1.5" />
      <circle cx="16" cy="16" r="10.5" fill="none" stroke="var(--color-ink)" strokeWidth="0.75" strokeDasharray="1.5 2.5" />
      <path d="M10.5 16.5 L14 20 L21.5 11.5" fill="none" stroke="var(--color-sage)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Header({ activeTab, onTabChange, onOpenAuth }) {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-rule bg-paper-raised/60 shadow-[0_1px_0_rgba(31,27,15,0.04),0_10px_24px_-18px_rgba(31,27,15,0.35)]">
      <div className="flex flex-wrap items-center justify-between gap-6 px-10 py-7">
        <div className="flex items-center gap-3.5">
          <SealMark />
          <div>
            <h1 className="font-display text-[28px] font-semibold leading-tight tracking-tight text-ink">
              Evidence Desk
            </h1>
            <div className="mt-0.5 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
              AI Meeting Documentation Platform
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-sm border border-sage/70 bg-sage-soft/40 px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.08em] text-sage">
            Every claim, sourced
          </div>

          {user ? (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-[13px] font-semibold text-ink">{user.email}</div>
                <div className="font-mono text-[10px] uppercase tracking-wide text-ink-soft">
                  {user.role}
                </div>
              </div>
              <button
                onClick={logout}
                className="rounded border border-rule px-3 py-1.5 text-[12px] font-semibold text-ink-soft transition-colors duration-200 hover:border-brick hover:text-brick"
              >
                Sign out
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="rounded bg-ink px-3.5 py-1.5 text-[12px] font-semibold text-white shadow-[0_4px_12px_-4px_rgba(31,59,87,0.5)] transition-all duration-200 hover:bg-[#16293c] hover:shadow-[0_6px_16px_-4px_rgba(31,59,87,0.6)]"
            >
              Sign in
            </button>
          )}
        </div>
      </div>

      <nav className="flex gap-1 px-10">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`border-b-2 px-4 py-2.5 text-[13.5px] font-semibold transition-colors duration-200 ${
              activeTab === tab.id
                ? 'border-ink text-ink'
                : 'border-transparent text-ink-soft hover:text-ink'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </header>
  );
}