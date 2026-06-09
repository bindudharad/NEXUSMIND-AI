import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXUSMIND AI | Autonomous Enterprise Intelligence & Digital Twin Platform",
  description: "Autonomous Enterprise Intelligence & Digital Twin Platform for strategic simulations, AI executives, Shadow Company planning, enterprise memory, and decision intelligence.",
  icons: {
    icon: "/favicon.svg",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
