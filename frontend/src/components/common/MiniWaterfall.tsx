import { useEffect, useRef } from "react";

// Animated sample waterfall -- decorative only, not real spectrum data.
// Throttled to ~8fps so several of these on one page stay cheap.
export function MiniWaterfall({ height = 64, colorSeed = 0 }: { height?: number; colorSeed?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    let frame = 0;

    function tick() {
      const rect = canvas!.getBoundingClientRect();
      const width = Math.max(1, Math.floor(rect.width));
      const heightPx = Math.max(1, Math.floor(rect.height));
      if (canvas!.width !== width || canvas!.height !== heightPx) {
        canvas!.width = width;
        canvas!.height = heightPx;
      }
      if (canvas!.height > 1) {
        const imageData = ctx!.getImageData(0, 0, canvas!.width, canvas!.height - 1);
        ctx!.putImageData(imageData, 0, 1);
      }
      for (let x = 0; x < canvas!.width; x++) {
        const noise = Math.sin(x / 8 + frame / 4 + colorSeed) * 0.5 + 0.5;
        const spike = Math.random() > 0.99 ? 1 : 0;
        const intensity = Math.min(1, noise * 0.55 + spike * 0.9 + Math.random() * 0.1);
        const hue = 200 - intensity * 170;
        ctx!.fillStyle = `hsl(${hue}, 90%, ${18 + intensity * 45}%)`;
        ctx!.fillRect(x, 0, 1, 1);
      }
      frame++;
    }

    const interval = setInterval(tick, 120);
    tick();
    return () => clearInterval(interval);
  }, [colorSeed]);

  return <canvas ref={canvasRef} style={{ width: "100%", height }} className="block rounded bg-black" />;
}
