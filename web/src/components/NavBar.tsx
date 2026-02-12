"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { getPages } from "@/lib/api";
import { useAnnotation, type AnnotationMode } from "@/lib/annotation-context";

export default function NavBar() {
  const pathname = usePathname();
  const segments = pathname.replace(/^\/|\/$/g, "").split("/").filter(Boolean);

  const isPageView =
    segments.length >= 4 &&
    segments[0] === "documents" &&
    segments[2] === "pages";
  const docName = segments[1] ?? "";
  const currentPage = isPageView ? segments[3] : null;

  const [pages, setPages] = useState<number[]>([]);
  const { mode, setMode } = useAnnotation();

  useEffect(() => {
    if (isPageView && docName) {
      getPages(docName).then(setPages).catch(() => {});
    }
  }, [isPageView, docName]);

  // Build breadcrumb
  const crumbs: { label: string; href?: string }[] = [];
  if (segments.length >= 2 && segments[0] === "documents") {
    crumbs.push({ label: "Home", href: "/" });
    crumbs.push({
      label: docName,
      href: segments.length > 2 ? `/documents/${docName}/` : undefined,
    });
  }

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-2">
      <a href="/" className="font-bold text-lg">
        PPX
      </a>
      <span className="text-xs text-gray-400 font-mono">{process.env.NEXT_PUBLIC_BUILD_VERSION}</span>
      {crumbs.length > 0 && (
        <>
          <span className="text-gray-300 mx-1">/</span>
          {crumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-2 text-sm">
              {i > 0 && <span className="text-gray-300">/</span>}
              {crumb.href ? (
                <a href={crumb.href} className="text-gray-500 hover:underline">
                  {crumb.label}
                </a>
              ) : (
                <span className="text-gray-700">{crumb.label}</span>
              )}
            </span>
          ))}
          {isPageView && (
            <>
              <span className="text-gray-300 text-sm">/</span>
              <select
                className="text-sm border border-gray-300 rounded px-2 py-0.5 bg-white text-gray-700 cursor-pointer"
                value={currentPage ?? ""}
                onChange={(e) => {
                  window.location.href = `/documents/${docName}/pages/${e.target.value}/`;
                }}
              >
                {pages.map((p) => (
                  <option key={p} value={p}>
                    Page {p}
                  </option>
                ))}
              </select>
            </>
          )}
        </>
      )}
      {isPageView && (
        <div className="ml-auto flex items-center gap-1 text-sm">
          <span className="text-gray-500 mr-1">OCR:</span>
          {([
            ["off", "Off"],
            ["line", "Lines"],
            ["word", "Words"],
          ] as [AnnotationMode, string][]).map(([value, label]) => (
            <button
              key={value}
              onClick={() => setMode(value)}
              className={`px-2.5 py-0.5 rounded border transition-colors ${
                mode === value
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-600 border-gray-300 hover:bg-gray-100"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </nav>
  );
}
