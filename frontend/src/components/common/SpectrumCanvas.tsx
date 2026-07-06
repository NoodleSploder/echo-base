import { useEffect, useRef } from "react";

// Animated sample spectrum trace + waterfall -- decorative only, not
// real spectrum data (see docs/PLUGIN_API.md / ROADMAP.md Phase 4).
export function SpectrumCanvas({ height = 260 }: { height?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    let frame = 0;
    const waterfallRows: number[][] = [];
    const bins = 200;

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

      const row: number[] = [];
      for (let i = 0; i < bins; i++) {
        const base = Math.sin(i / 14 + frame / 20) * 0.15 + 0.25;
        const peak = Math.sin(i / 3.3 + frame / 9) > 0.97 || Math.sin(i / 5.1 - frame / 13) > 0.98 ? Math.random() * 0.6 : 0;
        const noise = Math.random() * 0.08;
        row.push(Math.min(1, Math.max(0, base + peak + noise)));
      }
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
