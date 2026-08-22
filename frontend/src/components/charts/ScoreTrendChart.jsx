import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

const COLORS = {
  accent: "#4F46E5",
  safe: "#16A34A",
  warn: "#D97706",
  danger: "#DC2626",
  neutral: "#64748B",
};

// Distinct, legible slice colors for categorical breakdowns (failure
// category distribution, etc) -- cycles if there are more categories than
// colors.
const CATEGORY_PALETTE = [
  "#4F46E5", "#DC2626", "#D97706", "#16A34A", "#0891B2",
  "#7C3AED", "#DB2777", "#65A30D", "#EA580C", "#0D9488",
];

// Generic line chart for score-over-time / run-over-run trends. `data` is
// [{ label, value }, ...] -- deliberately shape-agnostic so both the
// Reliability Report and Regression pages can reuse it.
export function TrendLine({ data, dataKey = "value", color = "accent", height = 220 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid stroke="#E2E5EA" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#8A90A0" }}
          axisLine={{ stroke: "#E2E5EA" }}
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: "#8A90A0" }} axisLine={false} tickLine={false} width={32} />
        <Tooltip
          contentStyle={{ borderRadius: 8, borderColor: "#E2E5EA", fontSize: 12 }}
          labelStyle={{ color: "#12151C" }}
        />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke={COLORS[color] || color}
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Generic categorical bar chart, used e.g. for "tools by risk level" or
// "category score comparison" breakdowns.
export function CategoryBars({ data, dataKey = "value", color = "accent", height = 220 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid stroke="#E2E5EA" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "#8A90A0" }}
          axisLine={{ stroke: "#E2E5EA" }}
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: "#8A90A0" }} axisLine={false} tickLine={false} width={32} allowDecimals={false} />
        <Tooltip
          contentStyle={{ borderRadius: 8, borderColor: "#E2E5EA", fontSize: 12 }}
          labelStyle={{ color: "#12151C" }}
        />
        <Bar dataKey={dataKey} fill={COLORS[color] || color} radius={[4, 4, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  );
}

// Categorical pie/donut chart for distribution breakdowns, e.g. "failure
// category distribution". `data` is [{ label, value }, ...].
export function CategoryPie({ data, height = 240 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="label"
          innerRadius={50}
          outerRadius={90}
          paddingAngle={2}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip contentStyle={{ borderRadius: 8, borderColor: "#E2E5EA", fontSize: 12 }} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
