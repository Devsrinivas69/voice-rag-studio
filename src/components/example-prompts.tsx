const EXAMPLES = [
  "What is discussed in this dataset about education?",
  "What information is available about employment?",
  "Ask a question in Kannada.",
];

export function ExamplePrompts({ onPick }: { onPick: (text: string) => void }) {
  return (
    <section aria-labelledby="examples-heading" className="border-t border-border py-6">
      <h2 id="examples-heading" className="label-mono">
        Ask the dataset
      </h2>
      <p className="mt-2 text-sm text-muted-foreground">Use your voice to ask a question.</p>
      <ul className="mt-4 grid gap-2 sm:grid-cols-3">
        {EXAMPLES.map((e) => (
          <li key={e}>
            <button
              type="button"
              onClick={() => onPick(e)}
              className="h-full w-full border border-border bg-card/40 px-3 py-3 text-left text-sm text-foreground/80 transition-colors hover:border-border-strong hover:text-foreground"
            >
              {e}
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-muted-foreground">
        Examples fill the text fallback field — nothing is sent automatically.
      </p>
    </section>
  );
}
