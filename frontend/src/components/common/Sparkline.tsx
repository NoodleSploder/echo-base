export function Sparkline({
  data,
  className = "h-8 w-full",
  stroke = "#38bdf8",
}: {
  data: number[];
  className?: string;
  stroke?: string;
}) {
  if (data.length < 2) return null;

  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - ((value - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className={className}>
      <polyline points={points} fill="none" stroke={stroke} strokeWidth={4} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
