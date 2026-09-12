import { ItemCard } from './ItemCard';

const TYPE_ORDER = ['requirement', 'decision', 'action_item', 'risk', 'blocker', 'open_question'];

const TYPE_LABELS = {
  requirement: 'Requirements',
  decision: 'Decisions',
  action_item: 'Action Items',
  risk: 'Risks',
  blocker: 'Blockers',
  open_question: 'Open Questions',
};

function groupByType(items) {
  const groups = {};
  for (const item of items) {
    if (!groups[item.item_type]) groups[item.item_type] = [];
    groups[item.item_type].push(item);
  }
  return groups;
}

export function ExtractionPanel({ items, onAccept, onReject, onSaveEdit }) {
  const groups = groupByType(items);

  return (
    <div>
      {TYPE_ORDER.map((type) => {
        const groupItems = groups[type];
        if (!groupItems || groupItems.length === 0) return null;

        return (
          <div key={type} className="mb-7">
            <h3 className="mb-3 flex items-baseline justify-between border-b border-rule pb-1.5 font-display text-[15px] text-ink">
              {TYPE_LABELS[type]}
              <span className="font-mono text-[11px] text-ink-soft">
                {groupItems.length}
              </span>
            </h3>
            {groupItems.map((item) => (
              <ItemCard
                key={item.id}
                item={item}
                onAccept={onAccept}
                onReject={onReject}
                onSaveEdit={onSaveEdit}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}