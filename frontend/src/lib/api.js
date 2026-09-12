const BASE = '/api';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON — keep statusText
    }
    throw new ApiError(detail, res.status);
  }

  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  listMeetings: () => request('/transcripts'),

  uploadTranscript: (payload) =>
    request('/transcripts/upload', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getSegments: (meetingId) => request(`/transcripts/${meetingId}/segments`),

  runExtraction: (meetingId) =>
    request(`/meetings/${meetingId}/extract`, { method: 'POST' }),

  listExtractions: (meetingId) => request(`/meetings/${meetingId}/extractions`),

  reviewItem: (itemId, action, editedText) =>
    request(`/extractions/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({
        action,
        edited_text: editedText ?? null,
      }),
    }),

  previewMom: (meetingId) => request(`/meetings/${meetingId}/mom/preview`),

  downloadMomUrl: (meetingId) => `${BASE}/meetings/${meetingId}/mom/download`,
};

export { ApiError };