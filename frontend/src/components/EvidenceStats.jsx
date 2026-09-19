import { useCountUp } from '../lib/useCountUp';

function Stat({ glyph, value, decimals, suffix, label, delay }) {
  const count = useCountUp(value, { decimals, duration: 900 });
  return (
    <div className="reveal flex items-center gap-2.5" style={{ '--d': delay }}>
      <span className="font-display text-[22px] leading-none text-ink-soft">{glyph}</span>
      <div>
        <div className="font-mono text-[15px] font-semibold tabular-nums text-ink">
          {count}
          {suffix}
        </div>
        <div className="text-[10.5px] uppercase tracking-wide text-ink-soft">{label}</div>
      </div>
    </div>
  );
}

export function EvidenceStats({ segmentCount, extractedCount, acceptedCount, avgConfidence }) {
  return (
    <div className="mb-5 flex flex-wrap gap-x-8 gap-y-3 rounded-md border border-rule bg-paper-raised/60 px-5 py-3.5">
      <Stat glyph="§" value={segmentCount} label="Segments" delay="0.05s" />
      <Stat glyph="◇" value={extractedCount} label="Extracted" delay="0.11s" />
      <Stat glyph="✓" value={acceptedCount} label="Accepted" delay="0.17s" />
      <Stat glyph="%" value={avgConfidence} decimals={1} suffix="%" label="Avg. Confidence" delay="0.23s" />
    </div>
  );
}