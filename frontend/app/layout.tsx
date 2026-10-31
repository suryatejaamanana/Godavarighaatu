import type { Metadata } from "next";
import { Geist, Noto_Sans_Telugu } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const notoTelugu = Noto_Sans_Telugu({
  variable: "--font-telugu",
  subsets: ["telugu", "latin"],
});

export const metadata: Metadata = {
  title: "Godavari Ghaatu | గోదావరి ఘాటు",
  description: "Authentic Andhra Spice in Every Spoon",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${notoTelugu.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
