import { Home, Leaf, Truck, UtensilsCrossed } from "lucide-react";

// Wording is limited to what the brand has told us (poster and brief). Replace via the content
// manager when the owner supplies final copy (Phase 11).
const PROPS = [
  { icon: Home, title: "Home made", text: "Made the homemade way, in small batches." },
  { icon: UtensilsCrossed, title: "Authentic Andhra taste", text: "Village-style flavour in every spoon." },
  { icon: Leaf, title: "Traditional recipes", text: "Recipes from the Godavari region." },
  { icon: Truck, title: "Home delivery", text: "Delivered to your doorstep." },
];

export function ValueProps() {
  return (
    <ul className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {PROPS.map(({ icon: Icon, title, text }) => (
        <li key={title} className="rounded-2xl bg-white p-4 text-center shadow-sm ring-1 ring-brand-brown/10 sm:p-6">
          <span className="mx-auto mb-3 flex size-12 items-center justify-center rounded-full bg-brand-gold/30 text-brand-red">
            <Icon className="size-6" aria-hidden="true" />
          </span>
          <h3 className="font-display text-lg font-semibold uppercase tracking-wide text-brand-red">{title}</h3>
          <p className="mt-1 text-sm text-muted-foreground">{text}</p>
        </li>
      ))}
    </ul>
  );
}
