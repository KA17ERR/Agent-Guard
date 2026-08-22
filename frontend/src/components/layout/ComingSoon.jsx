import EmptyState from "../ui/EmptyState";

// Used by workflow pages whose backend step hasn't been wired into the
// frontend yet. Intentionally shows no data rather than mocking any —
// per the project's "no fake UI / no hardcoded results" rule, an honest
// empty state is preferable to a plausible-looking fake table.
export default function ComingSoon({ icon, title, description, requires }) {
  return (
    <EmptyState
      icon={icon}
      title={title}
      description={
        description ||
        `This step of the AgentGuard workflow will be wired up to ${requires} in a later build section.`
      }
    />
  );
}
