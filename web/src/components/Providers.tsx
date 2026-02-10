"use client";

import { AnnotationProvider } from "@/lib/annotation-context";

export default function Providers({ children }: { children: React.ReactNode }) {
  return <AnnotationProvider>{children}</AnnotationProvider>;
}
