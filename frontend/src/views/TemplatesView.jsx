import { useEffect, useState, useCallback, useRef } from 'react';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useToast } from '../lib/toast';
import { TemplateSectionCard } from '../components/TemplateSectionCard';

export function TemplatesView() {
  const { canReview } = useAuth();
  const showToast = useToast();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [name, setName] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      setTemplates(await api.listTemplates());
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTemplates(); }, [loadTemplates]);

  useEffect(() => {
    if (!selected) return;
    setDetailLoading(true);
    api.getTemplate(selected.id)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selected]);

  async function handleUpload() {
    if (!file) {
      showToast('Choose a .docx template file first.');
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('name', name.trim() || file.name);
      formData.append('file', file);
      const template = await api.uploadTemplate(formData);
      showToast(`Template learned — ${template.sections.length} sections classified.`);
      setName('');
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      await loadTemplates();
      setSelected(template);
      setDetail(template);
    } catch (e) {
      showToast('Upload failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="grid grid-cols-1 md:grid-cols-[340px_1fr]">
      <aside className="border-r border-rule px-6 py-6">
        <h2 className="font-display text-[17px] text-ink">Upload Template</h2>

        {canReview ? (
          <>
            <div className="mt-3">
              <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
                Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Acme SRS Template"
                className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
              />
            </div>
            <div className="mt-3">
              <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
                Template file (.docx)
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-[12.5px] file:mr-3 file:rounded file:border-0 file:bg-ink file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-white"
              />
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-3 w-full rounded bg-ink py-2.5 text-sm font-semibold text-white transition hover:bg-[#16293c] disabled:opacity-40"
            >
              {uploading ? 'Learning structure…' : 'Upload & Learn Structure'}
            </button>
            <div className="mt-2.5 rounded border border-dashed border-rule bg-paper px-2.5 py-2 font-mono text-[10.5px] text-ink-soft">
              Needs real Word heading styles (Heading 1, Heading 2, ...) to
              detect section boundaries. Every section is auto-classified —
              known types (Requirements, Decisions, Action Items, Risks,
              Participants), pure boilerplate (Purpose/Scope), or
              AI-drafted for anything else the template asks for.
            </div>
          </>
        ) : (
          <div className="mt-3 font-mono text-[10.5px] text-ink-soft">
            Sign in as a reviewer to upload templates.
          </div>
        )}

        <h2 className="mt-6 font-display text-[17px] text-ink">Templates</h2>
        <div className="mt-3">
          {loading && <span className="text-[12.5px] text-ink-soft">Loading…</span>}
          {!loading && templates.length === 0 && (
            <span className="text-[12.5px] text-ink-soft">No templates yet.</span>
          )}
          {!loading &&
            templates.map((t) => (
              <div
                key={t.id}
                onClick={() => setSelected(t)}
                className={`mb-1 cursor-pointer rounded-md border px-2.5 py-2 text-[13.5px] transition ${
                  selected?.id === t.id ? 'border-rule bg-paper-raised' : 'border-transparent hover:bg-paper-raised'
                }`}
              >
                <div className="font-semibold text-ink">{t.name}</div>
                <div className="font-mono text-[10.5px] text-ink-soft">
                  {t.section_count} sections · {t.original_filename}
                </div>
              </div>
            ))}
        </div>
      </aside>

      <section className="px-10 py-7 pb-16">
        {!selected ? (
          <div className="mt-20 text-center font-display text-lg text-ink-soft">
            Upload or select a template to see how its structure was learned.
          </div>
        ) : detailLoading ? (
          <div className="mt-20 text-center font-display text-lg text-ink-soft">Loading…</div>
        ) : detail ? (
          <div>
            <h2 className="font-display text-2xl text-ink">{detail.name}</h2>
            <div className="mt-1 font-mono text-[11.5px] text-ink-soft">
              {detail.original_filename} · {detail.sections.length} sections
            </div>

            <div className="mt-6">
              {detail.sections.map((section) => (
                <TemplateSectionCard key={section.id} section={section} />
              ))}
            </div>
          </div>
        ) : (
          <div className="mt-20 text-center font-display text-lg text-ink-soft">
            Could not load this template.
          </div>
        )}
      </section>
    </main>
  );
}