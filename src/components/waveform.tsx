export function Waveform({ levels }: { levels: number[] }) {
  const bars = 48;
  const data = Array.from({ length: bars }, (_, i) => levels[levels.length - bars + i] ?? 0);
  const hasSignal = levels.length > 0;

  if (!hasSignal) {
    return (
      <div className="label-mono h-10 leading-10" role="status">
        Recording indicator active
      </div>
    );
  }

  return (
    <div className="flex h-10 items-center justify-center gap-[2px]" aria-hidden="true">
      {data.map((v, i) => (
        <span
          key={i}
          className="w-[2px] rounded-full bg-primary/80"
          style={{ height: `${Math.max(2, v * 40)}px` }}
        />
      ))}
    </div>
  );
}
