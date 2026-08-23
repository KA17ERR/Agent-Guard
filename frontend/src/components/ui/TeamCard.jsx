import Card from "./Card";
import Icon from "./Icon";

function initials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

const SOCIAL_LINKS = [
  { key: "email", icon: "mail", label: "Email", href: (m) => `mailto:${m.email}` },
  { key: "linkedin", icon: "linkedin", label: "LinkedIn", href: (m) => m.linkedin },
  { key: "github", icon: "github", label: "GitHub", href: (m) => m.github },
  { key: "instagram", icon: "instagram", label: "Instagram", href: (m) => m.instagram },
];

export default function TeamCard({ member }) {
  return (
    <Card className="flex flex-col items-center gap-3 text-center">
      {member.photo ? (
        <img
          src={member.photo}
          alt={member.name}
          className="h-14 w-14 rounded-full border border-line object-cover"
        />
      ) : (
        <div className="flex h-14 w-14 items-center justify-center rounded-full border border-line bg-accent-soft text-sm font-semibold text-accent">
          {initials(member.name)}
        </div>
      )}
      <p className="text-sm font-medium text-ink">{member.name}</p>

      <div className="flex items-center gap-2">
        {SOCIAL_LINKS.filter((link) => member[link.key]).map((link) => (
          <a
            key={link.key}
            href={link.href(member)}
            target={link.key === "email" ? undefined : "_blank"}
            rel={link.key === "email" ? undefined : "noreferrer"}
            aria-label={`${member.name} on ${link.label}`}
            className="flex h-8 w-8 items-center justify-center rounded-md border border-line text-ink-faint transition-colors hover:border-accent hover:text-accent"
          >
            <Icon name={link.icon} className="h-4 w-4" />
          </a>
        ))}
      </div>
    </Card>
  );
}
