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
  safe: "#4ADE80",
  warn: "#FBBF24",
  danger: "#F87171",
  neutral: "#94A3B8",
};

// Distinct, legible slice colors for categorical breakdowns (failure
// category distribution, etc) -- cycles if there are more categories than
// colors.
const CATEGORY_PALETTE = [
  "#4F46E5", "#F87171", "#FBBF24", "#4ADE80", "#22D3EE",
  "#A78BFA", "#F472B6", "#A3E635", "#FB923C", "#2DD4BF",
];

// Dark-theme chart chrome, shared across all chart types below.
const GRID_STROKE = "#2A2E3A";
const AXIS_STROKE = "#2A2E3A";
const AXIS_TICK = { fontSize: 11, fill: "#A8ADBB" };
const TOOLTIP_STYLE = {
  backgroundColor: "#181B24",
  border: "1px solid #2A2E3A",
  borderRadius: 8,
  fontSize: 12,
  color: "#F4F5F7",
};
const TOOLTIP_LABEL_STYLE = { color: "#F4F5F7" };
const TOOLTIP_ITEM_STYLE = { color: "#A8ADBB" };
const LEGEND_STYLE = { fontSize: 11, color: "#A8ADBB" };

// Generic line chart for score-over-time / run-over-run trends. `data` is
// [{ label, value }, ...] -- deliberately shape-agnostic so both the
// Reliability Report and Regression pages can reuse it.
export function TrendLine({ data, dataKey = "value", color = "accent", height = 220 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
        <CartesianGrid stroke={GRID_STROKE} vertical={false} />
        <XAxis
          dataKey="label"
          tick={AXIS_TICK}
          axisLine={{ stroke: AXIS_STROKE }}
          tickLine={false}
        />
        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={32} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          labelStyle={TOOLTIP_LABEL_STYLE}
          itemStyle={TOOLTIP_ITEM_STYLE}
          cursor={{ stroke: GRID_STROKE }}
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
        <CartesianGrid stroke={GRID_STROKE} vertical={false} />
        <XAxis
          dataKey="label"
          tick={AXIS_TICK}
          axisLine={{ stroke: AXIS_STROKE }}
          tickLine={false}
        />
        <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} width={32} allowDecimals={false} />
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          labelStyle={TOOLTIP_LABEL_STYLE}
          itemStyle={TOOLTIP_ITEM_STYLE}
          cursor={{ fill: "rgba(255,255,255,0.04)" }}
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
        <Tooltip contentStyle={TOOLTIP_STYLE} labelStyle={TOOLTIP_LABEL_STYLE} itemStyle={TOOLTIP_ITEM_STYLE} />
        <Legend wrapperStyle={LEGEND_STYLE} />
      </PieChart>
    </ResponsiveContainer>
  );
}
