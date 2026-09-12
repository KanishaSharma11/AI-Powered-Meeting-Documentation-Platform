import { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { UploadPanel } from './components/UploadPanel';
import { MeetingList } from './components/MeetingList';
import { MeetingWorkspace } from './components/MeetingWorkspace';
import { ToastProvider } from './lib/toast';
import { api, ApiError } from './lib/api';

function AppInner() {
  const [meetings, setMeetings] = useState([]);
  const [meetingsLoading, setMeetingsLoading] = useState(true);
  const [meetingsError, setMeetingsError] = useState(null);
  const [selected, setSelected] = useState(null);

  const loadMeetings = useCallback(async () => {
    setMeetingsLoading(true);
    setMeetingsError(null);
    try {
      const data = await api.listMeetings();
      setMeetings(data);
    } catch (e) {
      setMeetingsError(e instanceof ApiError ? e.message : 'Unexpected error');
    } finally {
      setMeetingsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMeetings();
  }, [loadMeetings]);

  async function handleUploaded(meeting) {
    await loadMeetings();
    setSelected(meeting);
  }

  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <main className="grid grid-cols-1 md:grid-cols-[340px_1fr]">
        <aside className="border-r border-rule px-6 py-6">
          <UploadPanel onUploaded={handleUploaded} />
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
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AppInner />
    </ToastProvider>
  );
}