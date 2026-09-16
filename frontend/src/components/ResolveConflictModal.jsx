import { useState } from 'react';
import { api, ApiError } from '../lib/api';
import { useToast } from '../lib/toast';

export function ResolveConflictModal({ projectId, fact, onClose, onResolved }) {
  const showToast = useToast();
  const [choice, setChoice] = useState(fact.revisions[fact.revisions.length - 1]?.id || '');
  const [customText, setCustomText] = useState('');
  const [useCustom, setUseCustom] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleResolve() {
    setBusy(true);
    try {
      const payload = useCustom
        ? { custom_text: customText.trim() }
        : { chosen_revision_id: choice };

      if (useCustom && !customText.trim()) {
        showToast('Write the resolved text first.');
        setBusy(false);
        return;
      }

      await api.resolveConflict(projectId, fact.id, payload);
      showToast('Conflict resolved.');
      onResolved();
      onClose();
    } catch (e) {
      showToast('Resolve failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="animate-in w-full max-w-lg rounded-lg bg-paper-raised p-7 shadow-xl">
        <div className="mb-1 flex justify-between">
          <h2 className="font-display text-xl text-ink">Resolve Conflict</h2>
          <button onClick={onClose} className="text-ink-soft hover:text-ink">✕</button>
        </div>
        <div className="mb-5 font-mono text-[11px] uppercase tracking-wide text-brick">
          {fact.fact_type.replace('_', ' ')}
        </div>

        <div className="mb-4 space-y-2">
          {fact.revisions.map((rev) => (
            <label
              key={rev.id}
              className={`flex cursor-pointer items-start gap-2.5 rounded border px-3 py-2.5 transition ${
                !useCustom && choice === rev.id ? 'border-ink bg-paper' : 'border-rule'
              }`}
            >
              <input
                type="radio"
                name="revision"
                checked={!useCustom && choice === rev.id}
                onChange={() => { setChoice(rev.id); setUseCustom(false); }}
                className="mt-1"
              />
              <div>
                <div className="text-[13.5px] text-body">{rev.text}</div>
                <div className="mt-0.5 font-mono text-[10px] text-ink-soft">
                  {rev.relation} · {new Date(rev.created_at).toLocaleString()}
                </div>
              </div>
            </label>
          ))}

          <label className={`flex cursor-pointer items-start gap-2.5 rounded border px-3 py-2.5 transition ${useCustom ? 'border-ink bg-paper' : 'border-rule'}`}>
            <input type="radio" name="revision" checked={useCustom} onChange={() => setUseCustom(true)} className="mt-1" />
            <div className="flex-1">
              <div className="mb-1.5 text-[13.5px] font-semibold text-body">Write custom resolution</div>
              <textarea
                value={customText}
                onChange={(e) => { setCustomText(e.target.value); setUseCustom(true); }}
                rows={2}
                placeholder="Type the reconciled text..."
                className="w-full rounded border border-rule bg-paper-raised px-2 py-1.5 text-[13px] focus:outline-none focus:ring-2 focus:ring-ink/30"
              />
            </div>
          </label>
        </div>

        <button
          onClick={handleResolve}
          disabled={busy}
          className="w-full rounded bg-ink py-2.5 text-sm font-semibold text-white transition hover:bg-[#16293c] disabled:opacity-40"
        >
          {busy ? 'Resolving…' : 'Resolve'}
        </button>
      </div>
    </div>
  );
}