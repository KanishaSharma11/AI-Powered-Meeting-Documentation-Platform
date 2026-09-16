import { useState, useRef } from 'react';
import { api, ApiError } from '../lib/api';
import { useToast } from '../lib/toast';
import { useScreenAudioRecorder } from '../lib/useScreenAudioRecorder';

const PLACEHOLDER = `Sarah [00:00:05]: Let's discuss the login flow.
Raj [00:00:12]: We need OTP login support.
Sarah [00:00:20]: Agreed, approved for launch.`;

const MODES = [
  { id: 'text', label: 'Paste Text' },
  { id: 'file', label: 'Upload File' },
  { id: 'audio', label: 'Upload Audio' },
  { id: 'screen', label: 'Record Screen Audio' },
];

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

export function UploadPanel({ projects, onUploaded }) {
  const [mode, setMode] = useState('text');
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [projectId, setProjectId] = useState('');
  const [transcript, setTranscript] = useState('');
  const [file, setFile] = useState(null);
  const [audioSourceType, setAudioSourceType] = useState('meeting_bot_audio');
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef(null);
  const showToast = useToast();
  const recorder = useScreenAudioRecorder();

  function reset() {
    setTranscript('');
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    recorder.reset();
  }

  async function uploadBlobAsAudio(blob, filename, sourceType) {
    const formData = new FormData();
    const meetingTitle = title.trim() || 'Untitled Meeting';
    formData.append('title', meetingTitle);
    if (date) formData.append('meeting_date', date);
    if (projectId) formData.append('project_id', projectId);
    formData.append('source_type', sourceType);
    formData.append('file', blob, filename);
    return api.uploadTranscriptAudio(formData);
  }

  async function handleUpload() {
    if (mode === 'text' && !transcript.trim()) {
      showToast('Paste a transcript first.');
      return;
    }
    if ((mode === 'file' || mode === 'audio') && !file) {
      showToast('Choose a file first.');
      return;
    }
    if (mode === 'screen' && !recorder.recordedBlob) {
      showToast('Record something first, then stop the recording.');
      return;
    }

    setBusy(true);
    try {
      let meeting;
      const meetingTitle = title.trim() || 'Untitled Meeting';

      if (mode === 'text') {
        meeting = await api.uploadTranscriptText({
          title: meetingTitle,
          meeting_date: date || null,
          raw_transcript: transcript,
          project_id: projectId || null,
        });
      } else if (mode === 'file') {
        const formData = new FormData();
        formData.append('title', meetingTitle);
        if (date) formData.append('meeting_date', date);
        if (projectId) formData.append('project_id', projectId);
        formData.append('file', file);
        meeting = await api.uploadTranscriptFile(formData);
      } else if (mode === 'audio') {
        const formData = new FormData();
        formData.append('title', meetingTitle);
        if (date) formData.append('meeting_date', date);
        if (projectId) formData.append('project_id', projectId);
        formData.append('source_type', audioSourceType);
        formData.append('file', file);
        meeting = await api.uploadTranscriptAudio(formData);
      } else {
        meeting = await uploadBlobAsAudio(recorder.recordedBlob, 'screen-capture.webm', 'screen_share_audio');
      }

      showToast(`Uploaded — ${meeting.segment_count} segments normalized.`);
      reset();
      onUploaded(meeting);
    } catch (e) {
      showToast('Upload failed: ' + (e instanceof ApiError ? e.message : 'Unexpected error'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2 className="font-display text-[17px] text-ink">New Meeting</h2>

      <div className="mt-3 grid grid-cols-2 gap-1 rounded-md border border-rule bg-paper p-1">
        {MODES.map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={`rounded px-2 py-1.5 text-[11px] font-semibold leading-tight transition ${
              mode === m.id ? 'bg-ink text-white' : 'text-ink-soft hover:text-ink'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="mt-3.5">
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

      {projects.length > 0 && (
        <div className="mt-3.5">
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
            Project <span className="text-ink-soft/60">(optional)</span>
          </label>
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm text-body focus:outline-none focus:ring-2 focus:ring-ink/30"
          >
            <option value="">Standalone meeting</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>
      )}

      {mode === 'text' && (
        <div className="mt-3.5">
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
            Transcript
          </label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={PLACEHOLDER}
            rows={7}
            className="w-full resize-y rounded border border-rule bg-paper-raised px-2.5 py-2 font-mono text-[12.5px] text-body focus:outline-none focus:ring-2 focus:ring-ink/30"
          />
        </div>
      )}

      {mode === 'file' && (
        <div className="mt-3.5">
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
            Transcript file (.pdf, .docx, .txt, .md)
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-[12.5px] text-body file:mr-3 file:rounded file:border-0 file:bg-ink file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-white"
          />
        </div>
      )}

      {mode === 'audio' && (
        <>
          <div className="mt-3.5">
            <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
              Audio file (.wav, .mp3, .m4a)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-[12.5px] text-body file:mr-3 file:rounded file:border-0 file:bg-ink file:px-2.5 file:py-1 file:text-xs file:font-semibold file:text-white"
            />
          </div>
          <div className="mt-3.5">
            <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
              Capture method
            </label>
            <select
              value={audioSourceType}
              onChange={(e) => setAudioSourceType(e.target.value)}
              className="w-full rounded border border-rule bg-paper-raised px-2.5 py-2 text-sm text-body focus:outline-none focus:ring-2 focus:ring-ink/30"
            >
              <option value="meeting_bot_audio">Meeting recording (bot/full audio)</option>
              <option value="screen_share_audio">Screen-share / system audio capture</option>
            </select>
          </div>
        </>
      )}

      {mode === 'screen' && (
        <div className="mt-3.5">
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-soft">
            Live Screen/Tab Audio Capture
          </label>

          <div className="rounded border border-rule bg-paper px-3 py-3.5 text-center">
            {recorder.status === 'idle' && (
              <button
                onClick={recorder.start}
                className="rounded bg-brick px-4 py-2 text-[13px] font-semibold text-white transition hover:brightness-95"
              >
                ● Start Capture
              </button>
            )}

            {recorder.status === 'recording' && (
              <>
                <div className="mb-2.5 flex items-center justify-center gap-2 font-mono text-[13px] text-brick">
                  <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-brick" />
                  Recording {formatElapsed(recorder.elapsedSeconds)}
                </div>
                <button
                  onClick={recorder.stop}
                  className="rounded border border-ink px-4 py-2 text-[13px] font-semibold text-ink transition hover:bg-ink hover:text-white"
                >
                  ■ Stop
                </button>
              </>
            )}

            {recorder.status === 'stopped' && recorder.recordedBlob && (
              <div>
                <div className="mb-2 font-mono text-[12px] text-sage">
                  ✓ Captured {formatElapsed(recorder.elapsedSeconds)} of audio, ready to upload.
                </div>
                <button
                  onClick={recorder.reset}
                  className="rounded border border-rule px-3 py-1.5 text-[12px] font-semibold text-ink-soft transition hover:border-ink hover:text-ink"
                >
                  Discard & re-record
                </button>
              </div>
            )}

            {recorder.error && (
              <div className="mt-2.5 rounded border border-brick bg-brick-soft px-2.5 py-2 text-left text-[11.5px] text-brick">
                {recorder.error}
              </div>
            )}
          </div>

          <div className="mt-2.5 rounded border border-dashed border-rule bg-paper px-2.5 py-2 font-mono text-[10.5px] text-ink-soft">
            Your browser will prompt you to pick a tab/window/screen to
            share — tick "Share tab audio" (or equivalent) so the meeting
            audio is included. Whole-system audio support varies by
            browser/OS; capturing the specific browser tab running your
            call is the most reliable option. Nothing is transcribed
            until you click Upload below.
          </div>
        </div>
      )}

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