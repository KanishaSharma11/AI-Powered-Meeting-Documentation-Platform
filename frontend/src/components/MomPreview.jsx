function Section({ title, items, render }) {
  return (
    <>
      <h4 className="mb-1.5 mt-4.5 font-display text-[15px] text-ink first:mt-0">{title}</h4>
      {items && items.length > 0 ? (
        <ul className="mb-1.5 list-disc pl-5">
          {items.map((item, i) => (
            <li key={i} className="mb-1 text-[14px]">{render(item)}</li>
          ))}
        </ul>
      ) : (
        <div className="mb-1.5 font-body text-[13px] text-ink-soft">None recorded.</div>
      )}
    </>
  );
}

export function MomPreview({ mom, loading, error }) {
  if (loading) return <span className="text-[13px] text-ink-soft">Loading preview…</span>;
  if (error) return <span className="text-[13px] text-ink-soft">Preview unavailable: {error}</span>;
  if (!mom) return null;

  return (
    <div className="rounded-md border border-rule bg-paper-raised px-6.5 py-5.5 font-display text-sm">
      {mom.participants.length > 0 && (
        <>
          <h4 className="mb-1.5 font-display text-[15px] text-ink">Participants</h4>
          <div className="mb-1.5">{mom.participants.join(', ')}</div>
        </>
      )}
      <Section title="Requirements" items={mom.requirements} render={(r) => r.text} />
      <Section title="Decisions" items={mom.decisions} render={(d) => d.text} />
      <Section title="Action Items" items={mom.action_items} render={(a) =>
        `${a.text}${a.owner ? ' — ' + a.owner : ''}${a.due_date ? ' (' + a.due_date + ')' : ''}`
      } />
      <Section title="Risks & Open Questions" items={mom.risks} render={(r) => `[${r.category.replace('_', ' ')}] ${r.text}`} />
    </div>
  );
}