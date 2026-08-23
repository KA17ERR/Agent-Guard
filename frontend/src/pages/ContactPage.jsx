import Card, { CardHeader } from "../components/ui/Card";
import Icon from "../components/ui/Icon";
import TeamCard from "../components/ui/TeamCard";
import { TEAM } from "../utils/team";

export default function ContactPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Contact" subtitle="Get in touch with the team." />
        <p className="text-sm leading-relaxed text-ink-soft">
          Have a question, found a bug, or want to talk about a feature? Reach out any time.
        </p>
        <p className="mt-4 text-sm text-ink">
          <a href="mailto:support.agentguard@gmail.com" className="text-accent hover:underline">
            support.agentguard@gmail.com
          </a>
        </p>
      </Card>

      <Card rail="accent">
        <CardHeader
          title="Support"
          subtitle="Need help with a run, a scenario, or something not working as expected?"
        />
        <div className="space-y-3 text-sm leading-relaxed text-ink-soft">
          <div className="flex items-start gap-2.5">
            <Icon name="mail" className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <p>
              Email us directly at{" "}
              <a href="mailto:support.agentguard@gmail.com" className="text-accent hover:underline">
                support.agentguard@gmail.com
              </a>{" "}
              {/* TODO: point this at your real support inbox */}
              — we typically reply within one business day.
            </p>
          </div>
          <div className="flex items-start gap-2.5">
            <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <p>
              Found a bug? Include the agent name, the scenario or run ID if you have one, and
              what you expected to happen — it helps us track it down faster.
            </p>
          </div>
          <div className="flex items-start gap-2.5">
            <Icon name="github" className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
            <p>
              Prefer GitHub? Open an issue on our repo.{" "}
              {/* TODO: replace with your real repo URL */}
              <a
                href="https://github.com/KA17ERR/Agent-Guard"
                target="_blank"
                rel="noreferrer"
                className="text-accent hover:underline"
              >
                github.com/KA17ERR/Agent-Guard
              </a>
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="The team" subtitle="Reach out to any of us directly." />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {TEAM.map((member) => (
            <TeamCard key={member.name} member={member} />
          ))}
        </div>
      </Card>
    </div>
  );
}
