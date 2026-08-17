"use client";

import Link from "next/link";
import { Github } from "lucide-react";
import { DEMO_MODE } from "@/lib/api";

export function Header({ online }: { online: boolean | null }) {
  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="font-mono text-sm font-semibold tracking-[0.22em]">HHGOA</span>
          <span className="text-sm text-muted-foreground">Voice RAG</span>
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-6 sm:flex">
          <Link href="/" className="label-mono hover:text-foreground">
            Demo
          </Link>
          <Link href="/architecture" className="label-mono hover:text-foreground">
            Architecture
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer noopener"
            className="label-mono inline-flex items-center gap-1.5 hover:text-foreground"
            aria-label="GitHub repository"
          >
            <Github className="size-3.5" aria-hidden="true" /> GitHub
          </a>
        </nav>

        <div className="flex items-center gap-3">
          {DEMO_MODE && (
            <span className="label-mono rounded-xs border border-warning/50 px-1.5 py-0.5 text-warning">
              Demo mode
            </span>
          )}
          <span className="label-mono hidden md:inline">Task 02</span>
          <span className="label-mono inline-flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className={`size-1.5 rounded-full ${
                online === false ? "bg-destructive" : online ? "bg-success" : "bg-muted-foreground"
              }`}
            />
            {online === false ? "System offline" : online ? "System online" : "Checking"}
          </span>
        </div>
      </div>
    </header>
  );
}
