import { useState } from 'react';
import { useAuth, ApiError } from '../lib/auth';
import { useToast } from '../lib/toast';

export function AuthModal({ onClose }) {
  const { login, register } = useAuth();
  const showToast = useToast();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(email, password);
        showToast('Signed in.');
      } else {
        const me = await register(email, password);
        showToast(
          me.role === 'admin'
            ? "Registered - you're the first user, so you're an admin."
            : 'Registered - an admin can upgrade your role when needed.'
        );
      }
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="animate-in w-full max-w-sm rounded-lg bg-paper-raised p-7 shadow-xl">
        <div className="mb-5 flex justify-between">
          <h2 className="font-display text-xl text-ink">
            {mode === 'login' ? 'Sign in' : 'Create an account'}
          </h2>
          <button onClick={onClose} className="text-ink-soft hover:text-ink">✕</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-3.5">
            <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
            />
          </div>
          <div className="mb-4">
            <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
              Password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
            />
          </div>

          {error && (
            <div className="mb-3.5 rounded border border-brick bg-brick-soft px-3 py-2 text-[12.5px] text-brick">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded bg-ink py-2.5 text-sm font-semibold text-white transition hover:bg-[#16293c] disabled:opacity-40"
          >
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Register'}
          </button>
        </form>

        <div className="mt-4 text-center text-[12.5px] text-ink-soft">
          {mode === 'login' ? (
            <>
              No account?{' '}
              <button className="font-semibold text-ink underline" onClick={() => setMode('register')}>
                Register
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button className="font-semibold text-ink underline" onClick={() => setMode('login')}>
                Sign in
              </button>
            </>
          )}
        </div>

        {mode === 'register' && (
          <div className="mt-3 rounded border border-dashed border-rule bg-paper px-3 py-2 font-mono text-[10.5px] text-ink-soft">
            The very first account ever created on this system becomes admin
            automatically. Every account after that starts as a viewer — an
            admin can upgrade roles from there.
          </div>
        )}
      </div>
    </div>
  );
}