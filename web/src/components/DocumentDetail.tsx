"use client";

import { useEffect, useState } from "react";
import { getPages, getPageImageUrl } from "@/lib/api";

export default function DocumentDetail({ document }: { document: string }) {
  const [pages, setPages] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPages(document).then(setPages).catch((e) => setError(e.message));
  }, [document]);

  if (error) return <p className="text-red-600">Error: {error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{document}</h1>
      <p className="text-gray-500 mb-4">{pages.length} pages</p>
      {pages.length === 0 ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {pages.map((page) => (
            <a
              key={page}
              href={`/documents/${document}/pages/${page}/`}
              className="border rounded-lg overflow-hidden hover:shadow-md transition-shadow bg-white"
            >
              <img
                src={getPageImageUrl(document, page)}
                alt={`Page ${page}`}
                className="w-full"
              />
              <div className="p-2 text-center text-sm text-gray-600">
                Page {page}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
