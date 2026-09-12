import { useState } from 'react';
import { api, ApiError } from '../lib/api';
import { useToast } from '../lib/toast';

const PLACEHOLDER = `Sarah [00:00:05]: Let's discuss the login flow.
Raj [00:00:12]: We need OTP login support.
Sarah [00:00:20]: Agreed, approved for launch.

(Speaker [hh:mm:ss]: text — one line per turn. Timestamps optional.)`;

export function UploadPanel({ onUploaded }) {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [transcript, setTranscript] = useState('');
  const [busy, setBusy] = useState(false);
  const showToast = useToast();

  async function handleUpload() {
    if (!transcript.trim()) {
      showToast('Paste a transcript first.');
      return;
    }
    setBusy(true);
    try {
      const meeting = await api.uploadTranscript({
        title: title.trim() || 'Untitled Meeting',
        meeting_date: date || null,
        raw_transcript: transcript,
      });
      showToast(`Uploaded — ${meeting.segment_count} segments normalized.`);
      setTranscript('');
      onUploaded(meeting);
    } catch (e) {
      showToast(
        'Upload failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error')
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2 className="font-display text-[17px] text-ink">New Meeting</h2>

      <div className="mt-3">
        <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
          Title
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Requirements Workshop"
          className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm text-body focus:outline-none focus:ring-2 focus:ring-ink/30"
        />
      </div>

      <div className="mt-3.5">
        <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
          Date
        </label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm text-body focus:outline-none focus:ring-2 focus:ring-ink/30"
        />
      </div>

      <div className="mt-3.5">
        <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
          Transcript
        </label>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder={PLACEHOLDER}
          rows={8}
          className="w-full resize-y rounded border border-rule bg-paper-raised px-2.5 py-2 font-mono text-[12.5px] text-body focus:outline-none focus:ring-2 focus:ring-ink/30"
        />
      </div>

      <button
        onClick={handleUpload}
        disabled={busy}
        className="mt-3.5 w-full rounded bg-ink py-2.5 text-sm font-semibold text-white transition hover:bg-[#16293c] disabled:opacity-40"
      >
        {busy ? 'Uploading…' : 'Upload & Normalize'}
      </button>
    </div>
  );
}