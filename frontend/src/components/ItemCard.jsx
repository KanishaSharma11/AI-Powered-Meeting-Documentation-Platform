import { useState } from 'react';
import { useAuth } from '../lib/auth';

const STATUS_BORDER = {
  accepted: 'border-l-sage',
  edited: 'border-l-amber',
  rejected: 'border-l-brick',
  pending: 'border-l-rule',
};

export function ItemCard({ item, onAccept, onReject, onSaveEdit }) {
  const { canReview } = useAuth();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(item.final_text);
  const [justDecided, setJustDecided] = useState(false);

  const confPct = Math.round(item.combined_confidence * 100);
  const confClass = item.combined_confidence < 0.75 ? 'text-brick' : 'text-sage';
  const isRejected = item.review_status === 'rejected';

  function decide(action) {
    setJustDecided(true);
    action();
    setTimeout(() => setJustDecided(false), 300);
  }

  function startEdit() {
    setDraft(item.final_text);
    setEditing(true);
  }

  function save() {
    const text = draft.trim();
    if (!text) return;
    onSaveEdit(item.id, text);
    setEditing(false);
  }

  return (
    <div
      className={`card-raised card-raised-interactive mb-3 rounded-md border border-rule bg-paper-raised px-4 py-4 border-l-4 ${
        STATUS_BORDER[item.review_status] || STATUS_BORDER.pending
      } ${isRejected ? 'opacity-55' : ''} ${justDecided ? 'animate-stamp' : ''}`}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-2 rounded border border-dashed border-rule bg-paper px-2 py-1 font-mono text-[10.5px] text-ink-soft">
          <span>{item.segment_id || 'no evidence'}</span>
          <span>{item.evidence_speaker || '—'}</span>
          <span>{item.evidence_timestamp || '—'}</span>
          <span className={`font-semibold ${confClass}`}>{confPct}%</span>
        </span>
        {item.project_fact_id && (
          <span className="rounded-sm border border-plum bg-plum-soft px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide text-plum">
            fused to project
          </span>
        )}
      </div>

      {editing ? (
        <>
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={3}
            className="mb-3 w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm text-body focus:outline-none focus:ring-2 focus:ring-amber/40"
            autoFocus
          />
          <div className="flex gap-2">
            <button onClick={save} className="rounded border border-amber bg-amber-soft px-3 py-1.5 text-xs font-semibold text-amber transition-colors duration-200 hover:brightness-95">
              Save Edit
            </button>
            <button onClick={() => setEditing(false)} className="rounded border border-rule px-3 py-1.5 text-xs font-semibold text-ink-soft transition-colors duration-200 hover:border-ink">
              Cancel
            </button>
          </div>
        </>
      ) : (
        <>
          <div className="mb-3 text-[15px] leading-relaxed text-body">{item.final_text}</div>

          {item.item_type === 'action_item' && (
            <div className="-mt-1.5 mb-3 text-[12.5px] text-ink-soft">
              Owner: {item.owner || '—'} &nbsp;·&nbsp; Due: {item.due_date || '—'}
            </div>
          )}

          {canReview ? (
            <div className="flex flex-wrap gap-2">
              <button onClick={() => decide(() => onAccept(item.id))} disabled={item.review_status === 'accepted'}
                className="rounded border border-sage bg-sage-soft px-3 py-1.5 text-xs font-semibold text-sage transition-all duration-200 hover:brightness-95 hover:shadow-[0_4px_10px_-4px_rgba(88,122,92,0.5)] disabled:opacity-40 disabled:shadow-none">
                Accept
              </button>
              <button onClick={startEdit} className="rounded border border-amber bg-amber-soft px-3 py-1.5 text-xs font-semibold text-amber transition-all duration-200 hover:brightness-95 hover:shadow-[0_4px_10px_-4px_rgba(201,138,44,0.5)]">
                Edit
              </button>
              <button onClick={() => decide(() => onReject(item.id))} disabled={isRejected}
                className="rounded border border-brick bg-brick-soft px-3 py-1.5 text-xs font-semibold text-brick transition-all duration-200 hover:brightness-95 hover:shadow-[0_4px_10px_-4px_rgba(180,72,61,0.5)] disabled:opacity-40 disabled:shadow-none">
                Reject
              </button>
            </div>
          ) : (
            <div className="font-mono text-[10.5px] text-ink-soft">
              Sign in as a reviewer to accept, edit, or reject.
            </div>
          )}
        </>
      )}
    </div>
  );
}