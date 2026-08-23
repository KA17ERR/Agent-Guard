import { SiReact, SiVite, SiTailwindcss, SiGreensock, SiPython, SiFastapi } from "react-icons/si";
import LogoLoop from "../ui/LogoLoop";

// ---------------------------------------------------------------------------
// EDIT HERE to change which logos appear in the footer loop.
//
// Each entry is one of:
//   { node: <SomeIcon />, title: "Label", href: "https://..." }   — an icon
//   { src: "/logos/foo.png", alt: "Label", href: "https://..." }  — an image
//
// `href` is optional — drop it for a logo that shouldn't be a link.
// Icon components come from react-icons — browse more sets/icons at
// https://react-icons.github.io/react-icons (e.g. `import { SiOpenai } from
// "react-icons/si"` for another brand, or swap the `Si` set entirely for a
// different icon pack).
// ---------------------------------------------------------------------------
const FOOTER_LOGOS = [
  { node: <SiReact />, title: "React", href: "https://react.dev" },
  { node: <SiVite />, title: "Vite", href: "https://vitejs.dev" },
  { node: <SiTailwindcss />, title: "Tailwind CSS", href: "https://tailwindcss.com" },
  { node: <SiGreensock />, title: "GSAP", href: "https://gsap.com" },
  { node: <SiPython />, title: "Python", href: "https://www.python.org" },
  { node: <SiFastapi />, title: "FastAPI", href: "https://fastapi.tiangolo.com" },
];

export default function Footer() {
  return (
    <footer className="relative z-10 mt-10 px-4 py-6 sm:px-6">
      <LogoLoop
        logos={FOOTER_LOGOS}
        speed={90}
        direction="left"
        logoHeight={26}
        gap={48}
        hoverSpeed={20}
        scaleOnHover
        fadeOut
        fadeOutColor="#000000"
        ariaLabel="Technologies used to build AgentGuard"
        className="text-ink-soft"
      />
    </footer>
  );
}
