import { getSiteSettings } from "@/lib/site";

export async function AnnouncementBar() {
  const s = await getSiteSettings();
  if (!s.announcement) return null;
  return (
    <div className="bg-brand-brown px-4 py-1.5 text-center text-xs font-medium text-brand-gold sm:text-sm">
      {s.announcement}
      {s.announcementTe && <span className="ml-2 hidden text-brand-cream/80 sm:inline">· {s.announcementTe}</span>}
    </div>
  );
}
