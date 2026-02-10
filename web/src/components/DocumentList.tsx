"use client";

import { useEffect, useState } from "react";
import { getDocuments } from "@/lib/api";

export default function DocumentList() {
  const [documents, setDocuments] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDocuments().then(setDocuments).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-600">Error: {error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Documents</h1>
      {documents.length === 0 ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <li key={doc}>
              <a
                href={`/documents/${doc}/`}
                className="text-blue-600 hover:underline text-lg"
              >
                {doc}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
