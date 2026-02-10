"use client";

import { usePathname } from "next/navigation";
import DocumentList from "@/components/DocumentList";
import DocumentDetail from "@/components/DocumentDetail";
import PageDetail from "@/components/PageDetail";

export default function Router() {
  const pathname = usePathname();
  const segments = pathname.replace(/^\/|\/$/g, "").split("/").filter(Boolean);

  // /documents/:doc/pages/:page
  if (
    segments.length === 4 &&
    segments[0] === "documents" &&
    segments[2] === "pages"
  ) {
    return <PageDetail document={segments[1]} page={Number(segments[3])} />;
  }

  // /documents/:doc
  if (
    segments.length === 2 &&
    segments[0] === "documents" &&
    segments[1]
  ) {
    return <DocumentDetail document={segments[1]} />;
  }

  // / (home) or /documents/
  return <DocumentList />;
}
