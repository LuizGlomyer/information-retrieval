import { Hero } from "@/components/sections/Hero";
import { Pipeline } from "@/components/sections/Pipeline";
import { ModelsSection } from "@/components/sections/ModelsSection";
import { Metrics } from "@/components/sections/Metrics";
import { Playground } from "@/components/playground/Playground";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <SiteHeader />
      <main>
        <Hero />
        <Pipeline />
        <ModelsSection />
        <Metrics />
        <Playground />
      </main>
      <SiteFooter />
    </div>
  );
};

export default Index;
