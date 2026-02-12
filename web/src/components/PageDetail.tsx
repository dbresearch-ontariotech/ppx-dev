"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  getMarkdown,
  getPageImageUrl,
  getPages,
  getPageImageInfo,
  getOcrTexts,
  getOcrWords,
  type BBox,
} from "@/lib/api";
import { useAnnotation } from "@/lib/annotation-context";
import katex from "katex";
import "katex/dist/katex.min.css";

function renderLatex(html: string): string {
  // Display math: $$...$$
  html = html.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => {
    try {
      return katex.renderToString(tex, { displayMode: true, throwOnError: true });
    } catch {
      return `$$${tex}$$`;
    }
  });
  // Inline math: $...$  (but not $$)
  html = html.replace(/\$([^\$\n]+?)\$/g, (_, tex) => {
    try {
      return katex.renderToString(tex, { displayMode: false, throwOnError: true });
    } catch {
      return `$${tex}$`;
    }
  });
  return html;
}

export default function PageDetail({
  document,
  page,
}: {
  document: string;
  page: number;
}) {
  const router = useRouter();
  const { mode } = useAnnotation();
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [pages, setPages] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [splitPercent, setSplitPercent] = useState(50);
  const [imgSize, setImgSize] = useState<{ width: number; height: number } | null>(null);
  const [boxes, setBoxes] = useState<BBox[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const dragging = useRef(false);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (document) {
      getPages(document).then(setPages).catch(() => {});
    }
  }, [document]);

  useEffect(() => {
    if (document && !isNaN(page)) {
      getMarkdown(document, page)
        .then(setMarkdown)
        .catch((e) => setError(e.message));
      getPageImageInfo(document, page).then(setImgSize).catch(() => {});
    }
  }, [document, page]);

  useEffect(() => {
    if (mode === "off" || !document || isNaN(page)) {
      setBoxes([]);
      return;
    }
    const fetcher = mode === "line" ? getOcrTexts : getOcrWords;
    fetcher(document, page).then(setBoxes).catch(() => setBoxes([]));
  }, [mode, document, page]);

  const pageIndex = pages.indexOf(page);
  const hasPrev = pageIndex > 0;
  const hasNext = pageIndex >= 0 && pageIndex < pages.length - 1;
  const goTo = (p: number) => router.push(`/documents/${document}/pages/${p}`);

  const leftRef = useRef<HTMLDivElement>(null);
  const rightRef = useRef<HTMLDivElement>(null);

  const onMouseDown = useCallback(() => {
    dragging.current = true;
    setIsDragging(true);
  }, []);

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const pct = Math.min(80, Math.max(20, ((e.clientX - rect.left) / rect.width) * 100));
      if (leftRef.current) leftRef.current.style.width = `${pct}%`;
      if (rightRef.current) rightRef.current.style.width = `${100 - pct}%`;
    };
    const onMouseUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      setIsDragging(false);
      if (!containerRef.current || !leftRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const leftRect = leftRef.current.getBoundingClientRect();
      setSplitPercent((leftRect.width / rect.width) * 100);
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  if (error) return <p className="text-red-600">Error: {error}</p>;

  const mdHtml =
    markdown !== null
      ? (() => {
          const imgBase = `/api/documents/${document}/pages/${page}/imgs/`;
          const html = markdown
            .replace(/src="(?:\.\/)?imgs\//g, `src="${imgBase}`)
            .replace(/src='(?:\.\/)?imgs\//g, `src='${imgBase}`);
          return renderLatex(html);
        })()
      : null;

  return (
    <div className="h-full">
      <div
        ref={containerRef}
        className="flex h-full"
        style={{ userSelect: isDragging ? "none" : undefined }}
      >
        <div
          ref={leftRef}
          className="border rounded-lg overflow-hidden bg-white flex flex-col p-2"
          style={{ width: `${splitPercent}%` }}
        >
          <button
            disabled={!hasPrev}
            onClick={() => hasPrev && goTo(pages[pageIndex - 1])}
            className="shrink-0 py-1 px-3 text-sm rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Previous Page
          </button>
          <div className="flex-1 overflow-hidden min-h-0 my-1">
            <div className="relative h-full w-full flex items-center justify-center">
              <img
                ref={imgRef}
                src={getPageImageUrl(document, page)}
                alt={`Page ${page}`}
                className="max-w-full max-h-full object-contain block"
              />
              {mode !== "off" && imgSize && boxes.length > 0 && (
                <svg
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${imgSize.width} ${imgSize.height}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  {boxes.map((b, i) => (
                    <rect
                      key={i}
                      x={b.x0}
                      y={b.y0}
                      width={b.x1 - b.x0}
                      height={b.y1 - b.y0}
                      fill={mode === "line" ? "rgba(59,130,246,0.15)" : "rgba(234,88,12,0.15)"}
                      stroke={mode === "line" ? "#3b82f6" : "#ea580c"}
                      strokeWidth={2}
                    />
                  ))}
                </svg>
              )}
            </div>
          </div>
          <button
            disabled={!hasNext}
            onClick={() => hasNext && goTo(pages[pageIndex + 1])}
            className="shrink-0 py-1 px-3 text-sm rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Next Page
          </button>
        </div>

        <div
          className="w-1 mx-1 cursor-col-resize bg-gray-300 hover:bg-blue-400 rounded-full shrink-0 transition-colors"
          onMouseDown={onMouseDown}
        />

        {mdHtml === null ? (
          <div
            ref={rightRef}
            className="border rounded-lg bg-white p-6 text-sm font-mono whitespace-pre-wrap overflow-y-auto"
            style={{ width: `${100 - splitPercent}%` }}
          >
            <span className="text-gray-500">Loading markdown...</span>
          </div>
        ) : (
          <div
            ref={rightRef}
            className="markdown-panel border rounded-lg bg-white p-6 text-sm font-mono whitespace-pre-wrap overflow-y-auto [&_img]:!w-[80%] [&_img]:h-auto"
            style={{ width: `${100 - splitPercent}%` }}
            dangerouslySetInnerHTML={{ __html: mdHtml }}
          />
        )}
      </div>
    </div>
  );
}
