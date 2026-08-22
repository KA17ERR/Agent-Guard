// Minimal, dependency-free data table. `columns` is [{ key, header, render? }].
export default function Table({ columns, rows, rowKey = "id", onRowClick, emptyMessage = "No data yet." }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line py-10 text-center text-sm text-ink-faint">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-line bg-canvas text-xs uppercase tracking-wide text-ink-faint">
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-2.5 font-medium">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row[rowKey]}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-b border-line last:border-0 ${
                onRowClick ? "cursor-pointer hover:bg-canvas" : ""
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 align-middle text-ink-soft">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
