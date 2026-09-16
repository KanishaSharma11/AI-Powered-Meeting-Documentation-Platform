import { useEffect, useState, useCallback } from 'react';
import { api } from '../lib/api';
import { UploadPanel } from '../components/UploadPanel';
import { MeetingList } from '../components/MeetingList';
import { MeetingWorkspace } from '../components/MeetingWorkspace';

export function MeetingsView() {
  const [meetings, setMeetings] = useState([]);
  const [meetingsLoading, setMeetingsLoading] = useState(true);
  const [meetingsError, setMeetingsError] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);

  const loadMeetings = useCallback(async () => {
    setMeetingsLoading(true);
    setMeetingsError(null);
    try {
      const data = await api.listMeetings();
      setMeetings(data);
    } catch (e) {
      setMeetingsError(e.message || 'Unexpected error');
    } finally {
      setMeetingsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMeetings();
    api.listProjects().then(setProjects).catch(() => setProjects([]));
  }, [loadMeetings]);

  async function handleUploaded(meeting) {
    await loadMeetings();
    setSelected(meeting);
  }

  return (
    <main className="grid grid-cols-1 md:grid-cols-[340px_1fr]">
      <aside className="border-r border-rule px-6 py-6">
        <UploadPanel projects={projects} onUploaded={handleUploaded} />
        <MeetingList
          meetings={meetings}
          loading={meetingsLoading}
          error={meetingsError}
          selectedId={selected?.id}
          onSelect={setSelected}
        />
      </aside>

      <section className="px-10 py-7 pb-16">
        {selected ? (
          <MeetingWorkspace meeting={selected} />
        ) : (
          <div className="mt-20 text-center font-display text-lg text-ink-soft">
            Upload a transcript, or select a meeting on the left, to begin.
          </div>
        )}
      </section>
    </main>
  );
}