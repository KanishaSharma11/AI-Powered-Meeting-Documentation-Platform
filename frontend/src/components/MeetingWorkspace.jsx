import { useEffect, useState, useCallback } from 'react';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useToast } from '../lib/toast';
import { ExtractionPanel } from './ExtractionPanel';
import { MomPreview } from './MomPreview';
import { DocumentsPanel } from './DocumentsPanel';

const SECTIONS = [
  { id: 'review', label: 'Extraction & Review' },
  { id: 'mom', label: 'Fixed MOM (Stage 1/2)' },
  { id: 'documents', label: 'Generate Document (Stage 4/6)' },
];

export function MeetingWorkspace({ meeting }) {
  const { canReview } = useAuth();
  const showToast = useToast();
  const [section, setSection] = useState('review');

  const [items, setItems] = useState([]);
  const [itemsLoading, setItemsLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);

  const [mom, setMom] = useState(null);
  const [momLoading, setMomLoading] = useState(false);
  const [momError, setMomError] = useState(null);

  const loadExtractions = useCallback(async () => {
    setItemsLoading(true);
    try {
      const data = await api.listExtractions(meeting.id);
      setItems(data);
    } catch {
      setItems([]);
    } finally {
      setItemsLoading(false);
    }
  }, [meeting.id]);

  useEffect(() => { loadExtractions(); }, [loadExtractions]);

  const loadPreview = useCallback(async () => {
    setMomLoading(true);
    setMomError(null);
    try {
      const data = await api.previewMom(meeting.id);
      setMom(data);
    } catch (e) {
      setMomError(e instanceof ApiError ? e.message : 'Unexpected error');
    } finally {
      setMomLoading(false);
    }
  }, [meeting.id]);

  useEffect(() => {
    if (section === 'mom') loadPreview();
  }, [section, loadPreview]);

  async function handleExtract() {
    setExtracting(true);
    try {
      const result = await api.runExtraction(meeting.id);
      setItems(result.items);
      showToast(`Extraction complete — ${result.items.length} items found.`);
    } catch (e) {
      showToast('Extraction failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    } finally {
      setExtracting(false);
    }
  }

  async function handleAccept(itemId) {
    try {
      await api.reviewItem(itemId, 'accept');
      showToast('Item accepted.');
      loadExtractions();
    } catch (e) {
      showToast('Action failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    }
  }

  async function handleReject(itemId) {
    try {
      await api.reviewItem(itemId, 'reject');
      showToast('Item rejected.');
      loadExtractions();
    } catch (e) {
      showToast('Action failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    }
  }

  async function handleSaveEdit(itemId, text) {
    try {
      await api.reviewItem(itemId, 'edit', text);
      showToast('Edit saved.');
      loadExtractions();
    } catch (e) {
      showToast('Save failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    }
  }

  const approvedCount = items.filter((i) => i.review_status === 'accepted' || i.review_status === 'edited').length;

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl text-ink">{meeting.title}</h2>
          <div className="mt-1 font-mono text-[11.5px] text-ink-soft">
            {meeting.segment_count} transcript segments · source: {meeting.source_type}
          </div>
        </div>
        {canReview && (
          <button
            onClick={handleExtract}
            disabled={extracting}
            className="rounded border border-rule px-3.5 py-2 text-[13px] font-semibold text-ink transition hover:border-ink disabled:opacity-40"
          >
            {extracting ? 'Running agents…' : items.length > 0 ? 'Re-run Extraction' : 'Run Extraction'}
          </button>
        )}
      </div>

      <div className="mb-5 flex gap-1 border-b border-rule">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => setSection(s.id)}
            className={`border-b-2 px-3.5 py-2 text-[12.5px] font-semibold transition ${
              section === s.id ? 'border-ink text-ink' : 'border-transparent text-ink-soft hover:text-ink'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {section === 'review' && (
        itemsLoading ? (
          <div className="mt-16 text-center font-display text-lg text-ink-soft">Loading…</div>
        ) : items.length === 0 ? (
          <div className="mt-16 text-center font-display text-lg text-ink-soft">
            No extracted items yet. Run extraction to pull requirements, decisions,
            action items, and risks from this transcript.
          </div>
        ) : (
          <>
            <ExtractionPanel items={items} onAccept={handleAccept} onReject={handleReject} onSaveEdit={handleSaveEdit} />
            <div className="mt-3 font-mono text-[11px] text-ink-soft">
              {approvedCount} of {items.length} items accepted/edited so far.
            </div>
          </>
        )
      )}

      {section === 'mom' && (
        <div>
          <div className="mb-3.5 flex flex-wrap items-end justify-between gap-3">
            <div className="text-[12.5px] text-ink-soft">
              Fixed-layout MOM from accepted/edited items — always available, no template needed.
            </div>
            <a
              href={approvedCount > 0 ? api.downloadMomUrl(meeting.id) : undefined}
              target="_blank"
              rel="noreferrer"
              aria-disabled={approvedCount === 0}
              className={`rounded px-3.5 py-2 text-[13px] font-semibold text-white transition ${
                approvedCount === 0 ? 'pointer-events-none bg-ink/40' : 'bg-ink hover:bg-[#16293c]'
              }`}
            >
              Download MOM (.docx)
            </a>
          </div>
          <MomPreview mom={mom} loading={momLoading} error={momError} />
        </div>
      )}

      {section === 'documents' && <DocumentsPanel meetingId={meeting.id} />}
    </div>
  );
}