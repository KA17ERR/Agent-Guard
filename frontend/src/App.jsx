import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import AgentListPage from "./pages/agents/AgentListPage";
import AgentFormPage from "./pages/agents/AgentFormPage";
import ScenarioGenerationPage from "./pages/scenarios/ScenarioGenerationPage";
import TestExecutionPage from "./pages/execution/TestExecutionPage";
import TestResultsPage from "./pages/TestResultsPage";
import FailureDetailsPage from "./pages/failures/FailureDetailsPage";
import ReliabilityReportPage from "./pages/report/ReliabilityReportPage";
import RegressionPage from "./pages/RegressionPage";
import AboutPage from "./pages/AboutPage";
import ContactPage from "./pages/ContactPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />

        <Route path="/agents" element={<AgentListPage />} />
        <Route path="/agents/new" element={<AgentFormPage />} />
        <Route path="/agents/:agentId" element={<AgentFormPage />} />

        <Route path="/scenarios" element={<ScenarioGenerationPage />} />
        <Route path="/execution" element={<TestExecutionPage />} />
        <Route path="/results" element={<TestResultsPage />} />
        <Route path="/failures" element={<FailureDetailsPage />} />
        <Route path="/failures/:runId/:traceId" element={<FailureDetailsPage />} />
        <Route path="/report" element={<ReliabilityReportPage />} />
        <Route path="/regression" element={<RegressionPage />} />

        <Route path="/about" element={<AboutPage />} />
        <Route path="/contact" element={<ContactPage />} />

        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  );
}
