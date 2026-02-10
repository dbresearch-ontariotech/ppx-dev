"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

export type AnnotationMode = "off" | "line" | "word";

const AnnotationContext = createContext<{
  mode: AnnotationMode;
  setMode: (mode: AnnotationMode) => void;
}>({ mode: "off", setMode: () => {} });

export function AnnotationProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<AnnotationMode>("off");
  return (
    <AnnotationContext.Provider value={{ mode, setMode }}>
      {children}
    </AnnotationContext.Provider>
  );
}

export function useAnnotation() {
  return useContext(AnnotationContext);
}
