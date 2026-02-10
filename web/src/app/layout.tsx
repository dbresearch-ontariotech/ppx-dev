import type { Metadata } from "next";
import NavBar from "@/components/NavBar";
import Providers from "@/components/Providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "PPX — OCR Viewer",
  description: "Browse OCR pipeline results",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 h-screen flex flex-col overflow-hidden">
        <Providers>
          <NavBar />
          <main className="p-6 flex-1 overflow-hidden">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
