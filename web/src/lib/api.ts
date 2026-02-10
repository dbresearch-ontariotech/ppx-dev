const BASE = "/api";

export async function getDocuments(): Promise<string[]> {
  const res = await fetch(`${BASE}/documents`);
  if (!res.ok) throw new Error(`Failed to fetch documents: ${res.status}`);
  return res.json();
}

export async function getPages(document: string): Promise<number[]> {
  const res = await fetch(`${BASE}/documents/${document}/pages`);
  if (!res.ok) throw new Error(`Failed to fetch pages: ${res.status}`);
  return res.json();
}

export async function getMarkdown(
  document: string,
  page: number
): Promise<string> {
  const res = await fetch(`${BASE}/documents/${document}/pages/${page}/markdown`);
  if (!res.ok) throw new Error(`Failed to fetch markdown: ${res.status}`);
  const data = await res.json();
  return data.markdown;
}

export function getPageImageUrl(document: string, page: number): string {
  return `${BASE}/documents/${document}/pages/${page}/page.png`;
}

export interface BBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  text: string;
}

interface SplitFrame {
  columns: string[];
  data: (string | number)[][];
}

function parseBBoxes(frame: SplitFrame): BBox[] {
  const ci = (name: string) => frame.columns.indexOf(name);
  const ix0 = ci("x0"), iy0 = ci("y0"), ix1 = ci("x1"), iy1 = ci("y1"), itext = ci("text");
  return frame.data.map((row) => ({
    x0: row[ix0] as number,
    y0: row[iy0] as number,
    x1: row[ix1] as number,
    y1: row[iy1] as number,
    text: String(row[itext]),
  }));
}

export async function getOcrTexts(document: string, page: number): Promise<BBox[]> {
  const res = await fetch(`${BASE}/documents/${document}/pages/${page}/ocr/texts`);
  if (!res.ok) throw new Error(`Failed to fetch OCR texts: ${res.status}`);
  return parseBBoxes(await res.json());
}

export async function getOcrWords(document: string, page: number): Promise<BBox[]> {
  const res = await fetch(`${BASE}/documents/${document}/pages/${page}/ocr/words`);
  if (!res.ok) throw new Error(`Failed to fetch OCR words: ${res.status}`);
  return parseBBoxes(await res.json());
}

export async function getPageImageInfo(
  document: string,
  page: number
): Promise<{ width: number; height: number }> {
  const res = await fetch(`${BASE}/documents/${document}/pages/${page}/page.png/info`);
  if (!res.ok) throw new Error(`Failed to fetch image info: ${res.status}`);
  return res.json();
}
