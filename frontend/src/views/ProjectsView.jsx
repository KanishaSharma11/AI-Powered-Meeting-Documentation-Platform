import { useEffect, useState, useCallback } from 'react';
import { api, ApiError } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useToast } from '../lib/toast';
import { FactCard } from '../components/FactCard';
import { ResolveConflictModal } from '../components/ResolveConflictModal';

const FACT_TYPE_ORDER = ['requirement', 'decision', 'action_item', 'risk_or_question'];
const FACT_TYPE_LABELS = {
  requirement: 'Requirements', decision: 'Decisions',
  action_item: 'Action Items', risk_or_question: 'Risks & Open Questions',
};

export function ProjectsView() {
  const { canReview } = useAuth();
  const showToast = useToast();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [facts, setFacts] = useState([]);
  const [factsLoading, setFactsLoading] = useState(false);
  const [resolvingFact, setResolvingFact] = useState(null);

  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [creating, setCreating] = useState(false);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      setProjects(await api.listProjects());
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const loadFacts = useCallback(async (projectId) => {
    setFactsLoading(true);
    try {
      setFacts(await api.listProjectFacts(projectId));
    } catch {
      setFacts([]);
    } finally {
      setFactsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selected) loadFacts(selected.id);
  }, [selected, loadFacts]);

  async function handleCreate() {
    if (!newName.trim()) {
      showToast('Project name required.');
      return;
    }
    setCreating(true);
    try {
      const project = await api.createProject(newName.trim(), newDescription.trim() || null);
      showToast('Project created.');
      setNewName('');
      setNewDescription('');
      await loadProjects();
      setSelected(project);
    } catch (e) {
      showToast('Create failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    } finally {
      setCreating(false);
    }
  }

  const grouped = {};
  for (const f of facts) {
    if (!grouped[f.fact_type]) grouped[f.fact_type] = [];
    grouped[f.fact_type].push(f);
  }
  const conflictCount = facts.filter((f) => f.status === 'conflicted').length;

  return (
    <main className="grid grid-cols-1 md:grid-cols-[340px_1fr]">
      <aside className="border-r border-rule px-6 py-6">
        <h2 className="font-display text-[17px] text-ink">New Project</h2>
        {canReview ? (
          <>
            <div className="mt-3">
              <input
                type="text"
                placeholder="Project name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
              />
            </div>
            <div className="mt-2.5">
              <textarea
                placeholder="Description (optional)"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                rows={2}
                className="w-full resize-none rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ink/30"
              />
            </div>
            <button
              onClick={handleCreate}
              disabled={creating}
              className="mt-2.5 w-full rounded bg-ink py-2 text-[13px] font-semibold text-white transition hover:bg-[#16293c] disabled:opacity-40"
            >
              {creating ? 'Creating…' : 'Create Project'}
            </button>
          </>
        ) : (
          <div className="mt-3 font-mono text-[10.5px] text-ink-soft">
            Sign in as a reviewer to create projects.
          </div>
        )}

        <h2 className="mt-6 font-display text-[17px] text-ink">Projects</h2>
        <div className="mt-3">
          {loading && <span className="text-[12.5px] text-ink-soft">Loading…</span>}
          {!loading && projects.length === 0 && (
            <span className="text-[12.5px] text-ink-soft">No projects yet.</span>
          )}
          {!loading &&
            projects.map((p) => (
              <div
                key={p.id}
                onClick={() => setSelected(p)}
                className={`mb-1 cursor-pointer rounded-md border px-2.5 py-2 text-[13.5px] transition ${
                  selected?.id === p.id ? 'border-rule bg-paper-raised' : 'border-transparent hover:bg-paper-raised'
                }`}
              >
                <div className="font-semibold text-ink">{p.name}</div>
                <div className="font-mono text-[10.5px] text-ink-soft">{p.meeting_count} meetings</div>
              </div>
            ))}
        </div>
      </aside>

      <section className="px-10 py-7 pb-16">
        {!selected ? (
          <div className="mt-20 text-center font-display text-lg text-ink-soft">
            Create or select a project to see its reconciled knowledge.
          </div>
        ) : (
          <div>
            <h2 className="font-display text-2xl text-ink">{selected.name}</h2>
            {selected.description && <p className="mt-1 text-[13.5px] text-ink-soft">{selected.description}</p>}

            {conflictCount > 0 && (
              <div className="mt-3.5 rounded border border-brick bg-brick-soft px-3.5 py-2.5 text-[13px] text-brick">
                {conflictCount} fact{conflictCount !== 1 ? 's' : ''} need{conflictCount === 1 ? 's' : ''} conflict resolution.
              </div>
            )}

            <div className="mt-6">
              {factsLoading ? (
                <div className="mt-16 text-center font-display text-lg text-ink-soft">Loading…</div>
              ) : facts.length === 0 ? (
                <div className="mt-16 text-center font-display text-lg text-ink-soft">
                  No reconciled facts yet. Upload a meeting into this project and
                  accept/edit items — they'll appear here once reconciled.
                </div>
              ) : (
                FACT_TYPE_ORDER.map((type) => {
                  const items = grouped[type];
                  if (!items || items.length === 0) return null;
                  return (
                    <div key={type} className="mb-7">
                      <h3 className="mb-3 flex items-baseline justify-between border-b border-rule pb-1.5 font-display text-[15px] text-ink">
                        {FACT_TYPE_LABELS[type]}
                        <span className="font-mono text-[11px] text-ink-soft">{items.length}</span>
                      </h3>
                      {items.map((fact) => (
                        <FactCard key={fact.id} fact={fact} onResolveClick={setResolvingFact} />
                      ))}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </section>

      {resolvingFact && (
        <ResolveConflictModal
          projectId={selected.id}
          fact={resolvingFact}
          onClose={() => setResolvingFact(null)}
          onResolved={() => loadFacts(selected.id)}
        />
      )}
    </main>
  );
}