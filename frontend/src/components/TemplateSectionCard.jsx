const TYPE_STYLES = {
  requirement: 'border-ink bg-paper text-ink',
  decision: 'border-sage bg-sage-soft text-sage',
  action_item: 'border-amber bg-amber-soft text-amber',
  risk_or_question: 'border-brick bg-brick-soft text-brick',
  participants: 'border-plum bg-plum-soft text-plum',
  custom_text: 'border-rule bg-paper text-ink-soft',
  dynamic_custom: 'border-plum bg-plum-soft text-plum',
};

const TYPE_LABELS = {
  requirement: 'Requirement', decision: 'Decision', action_item: 'Action Item',
  risk_or_question: 'Risk / Question', participants: 'Participants',
  custom_text: 'Static Text', dynamic_custom: 'AI-Drafted (Dynamic)',
};

export function TemplateSectionCard({ section }) {
  return (
    <div className="mb-2 rounded-md border border-rule bg-paper-raised px-4 py-3">
      <div className="mb-1.5 flex items-center justify-between gap-2">
        <span className="font-display text-[14.5px] text-ink">
          {'  '.repeat(Math.max(0, section.heading_level - 1))}
          {section.heading_text}
        </span>
        <span className={`rounded-sm border px-1.5 py-0.5 font-mono text-[9px] uppercase ${TYPE_STYLES[section.content_type] || TYPE_STYLES.custom_text}`}>
          {TYPE_LABELS[section.content_type] || section.content_type}
        </span>
      </div>

      {section.is_table && section.table_columns && (
        <div className="font-mono text-[10.5px] text-ink-soft">
          Table columns: {section.table_columns.join(', ')}
        </div>
      )}

      {section.content_type === 'dynamic_custom' && section.custom_description && (
        <div className="mt-1 text-[12px] italic text-ink-soft">
          "{section.custom_description}"
        </div>
      )}

      {section.content_type === 'custom_text' && section.static_text && (
        <div className="mt-1 truncate text-[12px] text-ink-soft">
          {section.static_text}
        </div>
      )}
    </div>
  );
}