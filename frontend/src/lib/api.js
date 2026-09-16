const BASE = '/api';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

let authToken = null;
export function setAuthToken(token) {
  authToken = token;
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const res = await fetch(BASE + path, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // not JSON
    }
    throw new ApiError(detail, res.status);
  }

  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  }
  return res; // caller handles blob/stream (e.g. file downloads)
}

export const api = {
  // ---------- Auth (Stage 6) ----------
  register: (email, password) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),

  login: async (email, password) => {
    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try { detail = (await res.json()).detail || detail; } catch {}
      throw new ApiError(detail, res.status);
    }
    return res.json();
  },

  me: () => request('/auth/me'),

  setUserRole: (userId, newRole) =>
    request(`/auth/users/${userId}/role?new_role=${newRole}`, { method: 'PATCH' }),

  // ---------- Transcripts (Stage 1/2/5) ----------
  listMeetings: () => request('/transcripts'),

  uploadTranscriptText: (payload) =>
    request('/transcripts/upload', { method: 'POST', body: JSON.stringify(payload) }),

  uploadTranscriptFile: (formData) =>
    request('/transcripts/upload-file', { method: 'POST', body: formData }),

  uploadTranscriptAudio: (formData) =>
    request('/transcripts/upload-audio', { method: 'POST', body: formData }),

  getSegments: (meetingId) => request(`/transcripts/${meetingId}/segments`),

  // ---------- Extraction / review (Stage 1/2) ----------
  runExtraction: (meetingId) => request(`/meetings/${meetingId}/extract`, { method: 'POST' }),
  listExtractions: (meetingId) => request(`/meetings/${meetingId}/extractions`),
  reviewItem: (itemId, action, editedText) =>
    request(`/extractions/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({ action, edited_text: editedText ?? null }),
    }),

  // ---------- Fixed MOM (Stage 1/2 fallback) ----------
  previewMom: (meetingId) => request(`/meetings/${meetingId}/mom/preview`),
  downloadMomUrl: (meetingId) => `${BASE}/meetings/${meetingId}/mom/download`,

  // ---------- Projects / fusion (Stage 3) ----------
  listProjects: () => request('/projects'),
  createProject: (name, description) =>
    request('/projects', { method: 'POST', body: JSON.stringify({ name, description }) }),
  getProject: (projectId) => request(`/projects/${projectId}`),
  listProjectFacts: (projectId) => request(`/projects/${projectId}/facts`),
  resolveConflict: (projectId, factId, payload) =>
    request(`/projects/${projectId}/facts/${factId}/resolve`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),

  // ---------- Templates (Stage 4) ----------
  listTemplates: () => request('/templates'),
  getTemplate: (templateId) => request(`/templates/${templateId}`),
  uploadTemplate: (formData) => request('/templates/upload', { method: 'POST', body: formData }),

  // ---------- Documents / versioning (Stage 4/6) ----------
  generateDocument: (meetingId, templateId) =>
    request(`/meetings/${meetingId}/documents/generate?template_id=${templateId}`, { method: 'POST' }),
  listGeneratedDocuments: (meetingId) => request(`/meetings/${meetingId}/documents`),
  downloadDocumentUrl: (documentId) => `${BASE}/documents/${documentId}/download`,
};

export { ApiError };