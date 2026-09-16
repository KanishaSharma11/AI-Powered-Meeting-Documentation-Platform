import { useCallback, useRef, useState } from 'react';

/**
 * Captures system/tab audio directly from the browser (Section 2.3's
 * "screen-share + system audio capture" fallback source) — no Zoom/
 * Teams/Meet API credentials needed, since this is the browser's own
 * getDisplayMedia() picker, not a bot joining a call.
 *
 * BROWSER SUPPORT NOTES (real limitations, not a bug):
 *  - Chrome/Edge on Windows & Linux: can capture a shared TAB's audio
 *    reliably; whole-screen/system audio support varies by OS.
 *  - Chrome on macOS: tab audio capture works; full system audio
 *    capture generally does NOT (an OS-level limitation, not
 *    something fixable in this code).
 *  - Firefox: getDisplayMedia audio support is inconsistent across
 *    versions.
 *  - Safari: does not support capturing audio via getDisplayMedia at
 *    time of writing.
 * If the user's browser truly cannot capture audio, requestCapture()
 * still resolves (video-only), but the resulting recording will have
 * no audio track — recordingError surfaces this rather than silently
 * producing an empty transcript later.
 */
export function useScreenAudioRecorder() {
  const [status, setStatus] = useState('idle'); // idle | recording | stopped
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [error, setError] = useState(null);
  const [recordedBlob, setRecordedBlob] = useState(null);

  const streamRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const start = useCallback(async () => {
    setError(null);
    setRecordedBlob(null);
    setElapsedSeconds(0);

    if (!navigator.mediaDevices?.getDisplayMedia) {
      setError('This browser does not support screen/tab audio capture.');
      return;
    }

    try {
      // video: true is required by the spec on most browsers even
      // though we only keep the audio track — the picker UI is the
      // same one used for screen sharing in a call.
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true,
      });

      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        stream.getTracks().forEach((t) => t.stop());
        setError(
          'No audio track was captured. Make sure you tick "Share tab audio" (or equivalent) in the picker, and that your browser/OS supports it — see the note below.'
        );
        return;
      }

      streamRef.current = stream;
      chunksRef.current = [];

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        setStatus('stopped');
        cleanupStream();
      };

      // If the user stops sharing via the browser's own "Stop
      // sharing" bar (not our button), react the same as clicking Stop.
      stream.getVideoTracks()[0]?.addEventListener('ended', () => stop());

      recorderRef.current = recorder;
      recorder.start();
      setStatus('recording');

      timerRef.current = setInterval(() => {
        setElapsedSeconds((s) => s + 1);
      }, 1000);
    } catch (e) {
      if (e.name === 'NotAllowedError') {
        setError('Permission denied or picker cancelled.');
      } else {
        setError(e.message || 'Could not start capture.');
      }
    }
  }, [cleanupStream]);

  const stop = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
  }, []);

  const reset = useCallback(() => {
    cleanupStream();
    setStatus('idle');
    setElapsedSeconds(0);
    setError(null);
    setRecordedBlob(null);
    chunksRef.current = [];
  }, [cleanupStream]);

  return { status, elapsedSeconds, error, recordedBlob, start, stop, reset };
}