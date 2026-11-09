import type { Metadata } from "next";
import { Geist, Noto_Sans_Telugu, Oswald } from "next/font/google";
import "./globals.css";
import { BRAND_DEFAULTS, SITE_URL } from "@/lib/config";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const notoTelugu = Noto_Sans_Telugu({ variable: "--font-telugu", subsets: ["telugu", "latin"] });
// Condensed display face echoing the poster's bold headings
const oswald = Oswald({ variable: "--font-oswald", subsets: ["latin"], weight: ["500", "600", "700"] });

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${BRAND_DEFAULTS.name} | ${BRAND_DEFAULTS.nameTe}`,
    template: `%s | ${BRAND_DEFAULTS.name}`,
  },
  description: `${BRAND_DEFAULTS.label}. ${BRAND_DEFAULTS.tagline}.`,
  applicationName: BRAND_DEFAULTS.name,
  openGraph: { siteName: BRAND_DEFAULTS.name, type: "website", locale: "en_IN" },
  twitter: { card: "summary_large_image" },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${notoTelugu.variable} ${oswald.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
