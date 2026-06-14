"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ArxivTopBar } from "@/components/ArxivTopBar";
import { ChatMessageBody } from "@/components/ChatMessageBody";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { runChatBenchmark, formatLatencyMs, type BenchmarkResult, type PipelineMode } from "@/lib/chat-stream";
import { ArrowLeft, Play } from "lucide-react";

export default function DemoPage() {
  const params = useParams();
  const id = params.id as string;
  const [query, setQuery] = useState("What are the main findings across my uploaded papers?");
  const [pipelineMode, setPipelineMode] = useState<PipelineMode>("qa");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BenchmarkResult | null>(null);

  async function runBenchmark() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await runChatBenchmark(id, query.trim(), pipelineMode);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Benchmark failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="arxiv-mock arxiv-app-shell">
      <ArxivTopBar userInitials="D" />
      <div className="flex flex-1 flex-col overflow-y-auto p-6">
        <div className="mx-auto w-full max-w-5xl space-y-6">
          <div className="flex items-center gap-3">
            <Button type="button" variant="outline" size="sm" asChild>
              <Link href={`/projects/${id}`}>
                <ArrowLeft className="size-3.5" />
                Back to project
              </Link>
            </Button>
            <h1 className="font-serif text-lg">Fast vs Deep evaluation</h1>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Run comparison</CardTitle>
              <CardDescription>Same query, both modes — compare latency and answer quality side by side.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {(["qa", "literature_search", "synthesis"] as PipelineMode[]).map((m) => (
                  <Button
                    key={m}
                    type="button"
                    size="sm"
                    variant={pipelineMode === m ? "default" : "outline"}
                    onClick={() => setPipelineMode(m)}
                  >
                    {m}
                  </Button>
                ))}
              </div>
              <Textarea value={query} onChange={(e) => setQuery(e.target.value)} rows={3} className="text-sm" />
              <Button type="button" onClick={() => void runBenchmark()} disabled={loading}>
                <Play className="size-3.5" />
                {loading ? "Running…" : "Run Fast + Deep"}
              </Button>
              {error ? <p className="text-xs text-destructive">{error}</p> : null}
            </CardContent>
          </Card>

          {result ? (
            <div className="grid gap-4 md:grid-cols-2">
              {(["fast", "deep"] as const).map((mode) => {
                const row = result.results[mode];
                return (
                  <Card key={mode}>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm capitalize">{mode} mode</CardTitle>
                      <CardDescription className="font-mono text-xs">
                        {formatLatencyMs(row.latency_ms)} · {row.citations_count} sources
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ChatMessageBody content={row.answer || row.error || "(empty)"} variant="ai" />
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
