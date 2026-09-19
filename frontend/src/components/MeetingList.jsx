const SOURCE_LABELS = {
  official_transcript: 'Text',
  meeting_bot_audio: 'Audio',
  screen_share_audio: 'Screen',
};

export function MeetingList({ meetings, loading, error, selectedId, onSelect }) {
  return (
    <div className="mt-6">
      <h2 className="font-display text-[19px] text-ink">Meetings</h2>

      <div className="mt-3.5 space-y-1.5">
        {loading && <span className="text-[12.5px] text-ink-soft">Loading…</span>}

        {!loading && error && (
          <span className="text-[12.5px] text-brick">Could not reach API: {error}</span>
        )}

        {!loading && !error && meetings.length === 0 && (
          <span className="text-[12.5px] text-ink-soft">No meetings yet.</span>
        )}

        {!loading &&
          !error &&
          meetings.map((m) => (
            <div
              key={m.id}
              onClick={() => onSelect(m)}
              className={`cursor-pointer rounded-md border-l-[3px] px-3 py-2.5 text-[13.5px] transition-all duration-200 ${
                selectedId === m.id
                  ? 'card-raised border-l-ink bg-paper-raised'
                  : 'border-l-transparent hover:card-raised hover:bg-paper-raised'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="font-semibold text-ink">{m.title}</div>
                <span className="rounded-sm border border-rule px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide text-ink-soft">
                  {SOURCE_LABELS[m.source_type] || m.source_type}
                </span>
              </div>
              <div className="font-mono text-[10.5px] text-ink-soft">
                {m.segment_count} segments · {new Date(m.created_at).toLocaleDateString()}
                {m.project_id && <span className="ml-1.5 text-plum">· in project</span>}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}