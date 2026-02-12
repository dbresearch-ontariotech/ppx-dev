import { NextRequest } from "next/server";

const BACKEND = "http://localhost:8000";

async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const url = `${BACKEND}${path}${req.nextUrl.search}`;

  const res = await fetch(url, {
    method: req.method,
    headers: req.headers,
    body: req.body,
  });

  return new Response(res.body, {
    status: res.status,
    headers: {
      "content-type": res.headers.get("content-type") ?? "application/octet-stream",
    },
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;
