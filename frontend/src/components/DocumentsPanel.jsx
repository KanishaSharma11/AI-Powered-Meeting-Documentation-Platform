import { useEffect, useState, useCallback } from 'react';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useToast } from '../lib/toast';

export function DocumentsPanel({ meetingId }) {
  const { canReview } = useAuth();
  const showToast = useToast();
  const [templates, setTemplates] = useState([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadHistory = useCallback(async () => {
    try {
      const docs = await api.listGeneratedDocuments(meetingId);
      setHistory(docs);
    } catch {
      setHistory([]);
    }
  }, [meetingId]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [tpls] = await Promise.all([api.listTemplates(), loadHistory()]);
        setTemplates(tpls);
        if (tpls.length > 0) setSelectedTemplateId(tpls[0].id);
      } catch {
        setTemplates([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [meetingId, loadHistory]);

  async function handleGenerate() {
    if (!selectedTemplateId) {
      showToast('Upload a template first, under the Templates tab.');
      return;
    }
    setGenerating(true);
    try {
      const record = await api.generateDocument(meetingId, selectedTemplateId);
      showToast(`Generated version ${record.version}.`);
      loadHistory();
    } catch (e) {
      showToast('Generation failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    } finally {
      setGenerating(false);
    }
  }

  if (loading) return <span className="text-[13px] text-ink-soft">Loading templates…</span>;

  return (
    <div className="rounded-md border border-rule bg-paper-raised p-5">
      {templates.length === 0 ? (
        <div className="text-[13px] text-ink-soft">
          No templates uploaded yet. Go to the <strong>Templates</strong> tab to
          upload a client document template — its structure will be learned
          and reused for every meeting you generate a document for.
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[200px]">
              <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
                Template
              </label>
              <select
                value={selectedTemplateId}
                onChange={(e) => setSelectedTemplateId(e.target.value)}
                className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
              >
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>{t.name} ({t.section_count} sections)</option>
                ))}
              </select>
            </div>
            {canReview ? (
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="rounded bg-ink px-4 py-2 text-[13px] font-semibold text-white transition hover:bg-[#16293c] disabled:opacity-40"
              >
                {generating ? 'Generating…' : 'Generate New Version'}
              </button>
            ) : (
              <span className="font-mono text-[10.5px] text-ink-soft">Sign in as a reviewer to generate.</span>
            )}
          </div>

          <div className="mt-4 border-t border-rule pt-4">
            <h4 className="mb-2 font-display text-[14px] text-ink">Version History</h4>
            {history.length === 0 ? (
              <div className="text-[12.5px] text-ink-soft">No versions generated yet.</div>
            ) : (
              <div className="space-y-1.5">
                {history.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between rounded border border-rule bg-paper px-3 py-2">
                    <div>
                      <span className="font-mono text-[11px] font-semibold text-ink">v{doc.version}</span>
                      <span className="ml-2 text-[12.5px] text-ink-soft">
                        {doc.generated_by_email || 'unknown'} · {new Date(doc.generated_at).toLocaleString()}
                      </span>
                    </div>
                    <a
                      href={api.downloadDocumentUrl(doc.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded border border-rule px-2.5 py-1 text-[11.5px] font-semibold text-ink transition hover:border-ink"
                    >
                      Download
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}