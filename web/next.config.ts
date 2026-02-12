import type { NextConfig } from "next";

const isExport = process.env.NEXT_BUILD_MODE === "export";

const now = new Date();
const buildVersion = now.toLocaleString("en-US", {
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
  timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
}).replace(",", "");

const nextConfig: NextConfig = {
  ...(isExport ? { output: "export" } : {}),
  images: { unoptimized: true },
  trailingSlash: true,
  env: {
    NEXT_PUBLIC_BUILD_VERSION: buildVersion,
  },
};

export default nextConfig;
