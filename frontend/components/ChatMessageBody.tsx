"use client";

import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Section = {
  title: string | null;
  body: string;
};

function splitSections(content: string): Section[] {
  const trimmed = content.trim();
  if (!trimmed) return [];

  const matches = [...trimmed.matchAll(/^## (.+)$/gm)];
  if (matches.length === 0) {
    return [{ title: null, body: trimmed }];
  }

  const sections: Section[] = [];
  const firstIdx = matches[0].index ?? 0;
  if (firstIdx > 0) {
    const intro = trimmed.slice(0, firstIdx).trim();
    if (intro) sections.push({ title: null, body: intro });
  }

  for (let i = 0; i < matches.length; i++) {
    const title = matches[i][1].trim();
    const bodyStart = (matches[i].index ?? 0) + matches[i][0].length;
    const bodyEnd = i + 1 < matches.length ? (matches[i + 1].index ?? trimmed.length) : trimmed.length;
    sections.push({ title, body: trimmed.slice(bodyStart, bodyEnd).trim() });
  }

  return sections;
}

function MarkdownBlock({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn("chat-md", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h3 className="chat-md-h1">{children}</h3>,
          h2: ({ children }) => <h4 className="chat-md-h2">{children}</h4>,
          h3: ({ children }) => <h5 className="chat-md-h3">{children}</h5>,
          p: ({ children }) => <p className="chat-md-p">{children}</p>,
          ul: ({ children }) => <ul className="chat-md-ul">{children}</ul>,
          ol: ({ children }) => <ol className="chat-md-ol">{children}</ol>,
          li: ({ children }) => <li className="chat-md-li">{children}</li>,
          strong: ({ children }) => <strong className="chat-md-strong">{children}</strong>,
          blockquote: ({ children }) => <blockquote className="chat-md-quote">{children}</blockquote>,
          code: ({ className: codeClass, children, ...props }) => {
            const isBlock = codeClass?.includes("language-");
            if (isBlock) {
              return (
                <pre className="chat-md-pre">
                  <code className={codeClass} {...props}>
                    {children}
                  </code>
                </pre>
              );
            }
            return (
              <code className="chat-md-code" {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

type Props = {
  content: string;
  variant?: "user" | "ai";
};

export function ChatMessageBody({ content, variant = "ai" }: Props) {
  const sections = useMemo(() => splitSections(content), [content]);
  const hasSections = sections.some((s) => s.title);
  const [copied, setCopied] = useState(false);

  async function copyAll() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }

  if (variant === "user") {
    return <div className="mock-bub user whitespace-pre-wrap">{content}</div>;
  }

  return (
    <div className="chat-response group relative w-full">
      <div className="chat-response-toolbar">
        <Button type="button" variant="ghost" size="icon-xs" onClick={() => void copyAll()} aria-label="Copy message">
          {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
        </Button>
      </div>

      {!hasSections ? (
        <MarkdownBlock content={content} />
      ) : (
        <div className="chat-sections">
          {sections.map((section, idx) => {
            if (!section.title) {
              return section.body ? (
                <div key={`intro-${idx}`} className="chat-section-block">
                  <MarkdownBlock content={section.body} />
                </div>
              ) : null;
            }

            return (
              <section key={`${section.title}-${idx}`} className="chat-section-block">
                <h3 className="chat-section-title">{section.title}</h3>
                <div className="chat-section-desc">
                  <MarkdownBlock content={section.body} />
                </div>
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
