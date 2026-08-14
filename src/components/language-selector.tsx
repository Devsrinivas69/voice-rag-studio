import { LANGUAGES, type LanguageCode } from "@/types/api";

interface Props {
  value: LanguageCode;
  onChange: (code: LanguageCode) => void;
  disabled?: boolean;
}

export function LanguageSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="inline-flex items-center gap-2">
      <label htmlFor="language" className="label-mono">
        Language
      </label>
      <select
        id="language"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value as LanguageCode)}
        className="rounded-xs border border-border bg-surface px-2 py-1.5 font-mono text-xs text-foreground disabled:opacity-50"
      >
        {LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label} · {l.code}
          </option>
        ))}
      </select>
    </div>
  );
}
