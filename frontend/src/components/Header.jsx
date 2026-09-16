import { useAuth } from '../lib/auth';

const TABS = [
  { id: 'meetings', label: 'Meetings' },
  { id: 'projects', label: 'Projects' },
  { id: 'templates', label: 'Templates' },
];

export function Header({ activeTab, onTabChange, onOpenAuth }) {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-rule">
      <div className="flex flex-wrap items-baseline justify-between gap-5 px-10 py-6">
        <div>
          <h1 className="font-display text-[26px] font-bold tracking-tight text-ink">
            Evidence Desk
          </h1>
          <div className="mt-1 font-mono text-[11px] uppercase tracking-wider text-ink-soft">
            AI Meeting Documentation Platform
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-sm border border-sage px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-wide text-sage">
            Every claim, sourced
          </div>

          {user ? (
            <div className="flex items-center gap-2.5">
              <div className="text-right">
                <div className="text-[13px] font-semibold text-ink">{user.email}</div>
                <div className="font-mono text-[10px] uppercase tracking-wide text-ink-soft">
                  {user.role}
                </div>
              </div>
              <button
                onClick={logout}
                className="rounded border border-rule px-3 py-1.5 text-[12px] font-semibold text-ink-soft transition hover:border-brick hover:text-brick"
              >
                Sign out
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="rounded bg-ink px-3.5 py-1.5 text-[12px] font-semibold text-white transition hover:bg-[#16293c]"
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
            className={`border-b-2 px-4 py-2.5 text-[13.5px] font-semibold transition ${
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