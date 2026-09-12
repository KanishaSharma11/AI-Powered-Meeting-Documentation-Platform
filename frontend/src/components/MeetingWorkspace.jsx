import { useEffect, useState, useCallback } from 'react';
import { api, ApiError } from '../lib/api';
import { useToast } from '../lib/toast';
import { ExtractionPanel } from './ExtractionPanel';
import { MomPreview } from './MomPreview';

export function MeetingWorkspace({ meeting }) {
  const [items, setItems] = useState([]);
  const [itemsLoading, setItemsLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [mom, setMom] = useState(null);
  const [momLoading, setMomLoading] = useState(false);
  const [momError, setMomError] = useState(null);
  const showToast = useToast();

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

  useEffect(() => {
    loadExtractions();
  }, [loadExtractions]);

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
    if (items.length > 0) loadPreview();
  }, [items, loadPreview]);

  async function handleExtract() {
    setExtracting(true);
    try {
      const result = await api.runExtraction(meeting.id);
      setItems(result.items);
      showToast(`Extraction complete — ${result.items.length} items found.`);
    } catch (e) {
      showToast(
        'Extraction failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error')
      );
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

  const approvedCount = items.filter(
    (i) => i.review_status === 'accepted' || i.review_status === 'edited'
  ).length;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl text-ink">{meeting.title}</h2>
          <div className="mt-1 font-mono text-[11.5px] text-ink-soft">
            {meeting.segment_count} transcript segments · source: {meeting.source_type}
          </div>
        </div>
        <div className="flex flex-wrap gap-2.5">
          <button
            onClick={handleExtract}
            disabled={extracting}
            className="rounded border border-rule px-3.5 py-2 text-[13px] font-semibold text-ink transition hover:border-ink disabled:opacity-40"
          >
            {extracting ? 'Running agents…' : items.length > 0 ? 'Re-run Extraction' : 'Run Extraction'}
          </button>

          <a
            href={approvedCount > 0 ? api.downloadMomUrl(meeting.id) : undefined}
            target="_blank"
            rel="noreferrer"
            aria-disabled={approvedCount === 0}
            className={`rounded px-3.5 py-2 text-[13px] font-semibold text-white transition ${
              approvedCount === 0
                ? 'pointer-events-none bg-ink/40'
                : 'bg-ink hover:bg-[#16293c]'
            }`}
          >
            Download MOM (.docx)
          </a>
        </div>
      </div>

      {itemsLoading ? (
        <div className="mt-16 text-center font-display text-lg text-ink-soft">
          Loading…
        </div>
      ) : items.length === 0 ? (
        <div className="mt-16 text-center font-display text-lg text-ink-soft">
          No extracted items yet. Run extraction to pull requirements, decisions,
          action items, and risks from this transcript.
        </div>
      ) : (
        <>
          <ExtractionPanel
            items={items}
            onAccept={handleAccept}
            onReject={handleReject}
            onSaveEdit={handleSaveEdit}
          />

          <div className="mt-9 border-t border-rule pt-5">
            <div className="mb-3.5 flex flex-wrap items-end justify-between gap-3">
              <h2 className="font-display text-[19px] text-ink">MOM Preview</h2>
              <div className="text-[12.5px] text-ink-soft">
                {approvedCount} of {items.length} items accepted/edited — only these
                appear below.
              </div>
            </div>
            <MomPreview mom={mom} loading={momLoading} error={momError} />
          </div>
        </>
      )}
    </div>
  );
}