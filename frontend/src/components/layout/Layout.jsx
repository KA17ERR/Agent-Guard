import StaggeredMenu from "./StaggeredMenu";
import PageTransition from "./PageTransition";
import Footer from "./Footer";
import SoftAurora from "../backgrounds/SoftAurora";
import { NAV_ITEMS } from "../../utils/constants";

const menuItems = NAV_ITEMS.map((item) => ({
  label: item.label,
  ariaLabel: `Go to ${item.label}`,
  link: item.to,
}));

export default function Layout() {
  return (
    <div className="relative z-0 flex h-screen flex-col overflow-hidden">
      <div className="fixed inset-0 -z-10 bg-black">
        <SoftAurora
          speed={0.6}
          scale={1.5}
          brightness={1}
          color1="#f7f7f7"
          color2="#e100ff"
          noiseFrequency={2.5}
          noiseAmplitude={1}
          bandHeight={0.5}
          bandSpread={1}
          octaveDecay={0.1}
          layerOffset={0}
          colorSpeed={1}
          enableMouseInteraction
          mouseInfluence={0.25}
        />
      </div>

      <StaggeredMenu
        position="right"
        items={menuItems}
        displayItemNumbering
        displaySocials={false}
        accentColor="#4F46E5"
        colors={["#0F1117", "#1B1E28"]}
      />

      <main id="app-scroll-container" className="relative z-10 flex-1 overflow-y-auto">
        <div className="flex min-h-full flex-col">
          <div className="flex-1 px-4 py-6 sm:px-6">
            <PageTransition />
          </div>
          <Footer />
        </div>
      </main>
    </div>
  );
}
