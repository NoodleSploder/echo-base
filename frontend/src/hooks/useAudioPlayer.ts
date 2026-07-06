import { useEffect, useRef, useState } from "react";

const SAMPLE_RATE_HZ = 48_000;
const LEVEL_UPDATE_EVERY_N_CHUNKS = 3;

function chunkRms(pcm16: Int16Array): number {
  let sumSquares = 0;
  for (let i = 0; i < pcm16.length; i++) {
    const normalized = pcm16[i] / 32768;
    sumSquares += normalized * normalized;
  }
  return pcm16.length ? Math.sqrt(sumSquares / pcm16.length) : 0;
}

// Plays a receiver's demodulated PCM16 audio stream (/ws/audio/{id})
// through the Web Audio API. Each incoming chunk is scheduled back to
// back against a running cursor (nextStartTime) rather than played
// immediately, which is what keeps chunk-to-chunk playback gapless
// despite each WebSocket message arriving as a separate ~20ms buffer.
//
// `squelch` (0-1, RMS threshold) mutes playback while the signal is
// below it -- read via a ref so adjusting the slider doesn't tear down
// and reconnect the WebSocket.
export function useAudioPlayer(
  receiverId: string | null,
  mode: string,
  enabled: boolean,
  squelch: number,
) {
  const [connected, setConnected] = useState(false);
  const [level, setLevel] = useState(0);
  const squelchRef = useRef(squelch);
  squelchRef.current = squelch;

  useEffect(() => {
    setConnected(false);
    setLevel(0);
    if (!enabled || !receiverId) return;
    const id = receiverId;

    let cancelled = false;
    let chunkCount = 0;
    const audioContext = new AudioContext();
    let nextStartTime = audioContext.currentTime;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
      `${protocol}://${window.location.host}/ws/audio/${encodeURIComponent(id)}?mode=${mode}`,
    );
    socket.binaryType = "arraybuffer";

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => socket.close();
    socket.onmessage = (message) => {
      if (cancelled || !(message.data instanceof ArrayBuffer)) return;

      const pcm16 = new Int16Array(message.data);
      const rms = chunkRms(pcm16);

      chunkCount++;
      if (chunkCount % LEVEL_UPDATE_EVERY_N_CHUNKS === 0) setLevel(rms);

      if (rms < squelchRef.current) return; // squelched: track level, don't play

      const pcmFloat = new Float32Array(pcm16.length);
      for (let i = 0; i < pcm16.length; i++) pcmFloat[i] = pcm16[i] / 32768;

      const buffer = audioContext.createBuffer(1, pcmFloat.length, SAMPLE_RATE_HZ);
      buffer.copyToChannel(pcmFloat, 0);

      const source = audioContext.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContext.destination);

      const startAt = Math.max(nextStartTime, audioContext.currentTime);
      source.start(startAt);
      nextStartTime = startAt + buffer.duration;
    };

    return () => {
      cancelled = true;
      socket.close();
      void audioContext.close();
    };
  }, [receiverId, mode, enabled]);

  return { connected, level };
}
