import { useState } from 'react';
import { useAuth } from '../lib/auth';

export function FactCard({ fact, onResolveClick }) {
  const { canReview } = useAuth();
  const [expanded, setExpanded] = useState(false);
  const isConflicted = fact.status === 'conflicted';

  return (
    <div
      className={`mb-2.5 rounded-md border bg-paper-raised px-4 py-3.5 border-l-4 ${
        isConflicted ? 'border-l-brick border-brick/30' : 'border-l-sage border-rule'
      }`}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span
          className={`rounded-sm border px-1.5 py-0.5 font-mono text-[9px] uppercase ${
            isConflicted ? 'border-brick bg-brick-soft text-brick' : 'border-sage bg-sage-soft text-sage'
          }`}
        >
          {isConflicted ? 'Conflicted — needs review' : 'Active'}
        </span>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="font-mono text-[10.5px] text-ink-soft hover:text-ink"
        >
          {fact.revisions.length} mention{fact.revisions.length !== 1 ? 's' : ''} {expanded ? '▲' : '▼'}
        </button>
      </div>

      <div className="mb-2 text-[14.5px] text-body">{fact.canonical_text}</div>

      {fact.item_type === 'action_item' && (fact.owner || fact.due_date) && (
        <div className="mb-2 text-[12.5px] text-ink-soft">
          Owner: {fact.owner || '—'} · Due: {fact.due_date || '—'}
        </div>
      )}

      {expanded && (
        <div className="mt-2.5 space-y-1.5 border-t border-rule pt-2.5">
          {fact.revisions.map((rev) => (
            <div key={rev.id} className="rounded bg-paper px-2.5 py-2">
              <div className="text-[12.5px] text-body">{rev.text}</div>
              <div className="mt-0.5 font-mono text-[10px] text-ink-soft">
                {rev.relation} · {new Date(rev.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {isConflicted && canReview && (
        <button
          onClick={() => onResolveClick(fact)}
          className="mt-2.5 rounded border border-brick bg-brick-soft px-3 py-1.5 text-xs font-semibold text-brick transition hover:brightness-95"
        >
          Resolve Conflict
        </button>
      )}
    </div>
  );
}