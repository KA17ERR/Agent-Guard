import { motion } from "motion/react";
import logo from "../assets/logo-shield.svg";
import Card, { CardHeader } from "../components/ui/Card";
import CircularText from "../components/ui/CircularText";
import TeamCard from "../components/ui/TeamCard";
import { TEAM } from "../utils/team";

export default function AboutPage() {
  return (
    <div className="space-y-6">
      {/* Logo hero — same spinning ring + glow treatment as the page loader */}
      <div className="flex flex-col items-center gap-4 py-6">
        <div className="relative flex h-[200px] w-[200px] items-center justify-center">
          <CircularText
            text="AGENTGUARD*RELIABILITY*ENGINE*"
            onHover="speedUp"
            spinDuration={20}
            className="text-[13px] tracking-widest drop-shadow-[0_0_6px_rgba(99,102,241,0.65)]"
          />

          <div className="absolute inset-0 flex items-center justify-center">
            {[0, 0.35].map((delay) => (
              <motion.span
                key={delay}
                className="absolute h-16 w-16 rounded-full border-2 border-accent/50"
                initial={{ scale: 0.8, opacity: 0.7 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{ duration: 1.3, repeat: Infinity, ease: "easeOut", delay }}
              />
            ))}
            <img
              src={logo}
              alt="AgentGuard"
              className="relative h-14 w-14 rounded-2xl"
              style={{ boxShadow: "0 0 32px rgba(79, 70, 229, 0.65)" }}
            />
          </div>
        </div>
      </div>

      <Card>
        <CardHeader title="About AgentGuard" subtitle="What this tool is for." />
         <p className="text-sm leading-relaxed text-ink-soft">
          AgentGuard is a reliability-testing tool for AI agents. It generates adversarial and
          realistic test scenarios from an agent's system prompt, domain, and tools, runs them
          against the agent, and reports where it fails — prompt injection, tool misuse, goal
          drift, hallucination, and more — so issues get caught before they reach production.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-ink-soft">
          Most teams ship an agent after testing a handful of happy-path conversations by hand.
          That catches obvious bugs, but it says nothing about what happens when a user is vague,
          adversarial, or simply asks for something the agent should refuse. AgentGuard exists to
          close that gap — it treats reliability testing the way traditional software treats unit
          testing: automated, repeatable, and run before every release rather than after an
          incident.
        </p>
      </Card>

      <Card>
        <CardHeader title="Meet the team" subtitle="The people building AgentGuard." />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {TEAM.map((member) => (
            <TeamCard key={member.name} member={member} />
          ))}
        </div>
      </Card>
    </div>
  );
}
