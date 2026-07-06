import { useEffect, useRef } from "react";

const SYNTHETIC_BINS = 200;

// Renders either a real FFT magnitude frame (see useSpectrumStream) or,
// when none is available, an animated decorative trace + waterfall
// (see docs/PLUGIN_API.md / ROADMAP.md Phase 4 -- IQ streaming).
export function SpectrumCanvas({
  height = 260,
  liveFrame = null,
}: {
  height?: number;
  liveFrame?: Float32Array | null;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const liveFrameRef = useRef<Float32Array | null>(null);
  liveFrameRef.current = liveFrame;

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    let frame = 0;
    const waterfallRows: number[][] = [];

    function syntheticRow(): number[] {
      const row: number[] = [];
      for (let i = 0; i < SYNTHETIC_BINS; i++) {
        const base = Math.sin(i / 14 + frame / 20) * 0.15 + 0.25;
        const peak =
          Math.sin(i / 3.3 + frame / 9) > 0.97 || Math.sin(i / 5.1 - frame / 13) > 0.98
            ? Math.random() * 0.6
            : 0;
        const noise = Math.random() * 0.08;
        row.push(Math.min(1, Math.max(0, base + peak + noise)));
      }
      return row;
    }

    function normalizedLiveRow(live: Float32Array): number[] {
      let min = Infinity;
      let max = -Infinity;
      for (const value of live) {
        if (value < min) min = value;
        if (value > max) max = value;
      }
      const range = Math.max(max - min, 1e-6);
      return Array.from(live, (value) => (value - min) / range);
    }

    function tick() {
      const rect = canvas!.getBoundingClientRect();
      const width = Math.max(1, Math.floor(rect.width));
      const h = Math.max(1, Math.floor(rect.height));
      if (canvas!.width !== width || canvas!.height !== h) {
        canvas!.width = width;
        canvas!.height = h;
      }

      const traceHeight = Math.floor(h * 0.35);
      const waterfallHeight = h - traceHeight;

      const live = liveFrameRef.current;
      const row = live ? normalizedLiveRow(live) : syntheticRow();
      const bins = row.length;

      waterfallRows.unshift(row);
      if (waterfallRows.length > waterfallHeight) waterfallRows.length = waterfallHeight;

      ctx!.fillStyle = "#05070a";
      ctx!.fillRect(0, 0, width, h);

      ctx!.beginPath();
      row.forEach((value, i) => {
        const x = (i / (bins - 1)) * width;
        const y = traceHeight - value * traceHeight;
        if (i === 0) ctx!.moveTo(x, y);
        else ctx!.lineTo(x, y);
      });
      const gradient = ctx!.createLinearGradient(0, 0, width, 0);
      gradient.addColorStop(0, "#34d399");
      gradient.addColorStop(0.4, "#38bdf8");
      gradient.addColorStop(0.7, "#a78bfa");
      gradient.addColorStop(1, "#fb923c");
      ctx!.strokeStyle = gradient;
      ctx!.lineWidth = 1.5;
      ctx!.stroke();

      const binWidth = Math.ceil(width / bins);
      for (let r = 0; r < waterfallRows.length; r++) {
        const dataRow = waterfallRows[r];
        for (let i = 0; i < dataRow.length; i++) {
          const value = dataRow[i];
          const x = Math.floor((i / (bins - 1)) * width);
          const hue = 200 - value * 170;
          ctx!.fillStyle = `hsl(${hue}, 90%, ${15 + value * 45}%)`;
          ctx!.fillRect(x, traceHeight + r, binWidth, 1);
        }
      }

      frame++;
    }

    const interval = setInterval(tick, 120);
    tick();
    return () => clearInterval(interval);
  }, []);

  return <canvas ref={canvasRef} style={{ width: "100%", height }} className="block rounded" />;
}
