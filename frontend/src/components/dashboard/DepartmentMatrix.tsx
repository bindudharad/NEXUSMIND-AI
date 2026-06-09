"use client";

import type { DepartmentSignal } from "@/types/dashboard";

const rows: Array<keyof Omit<DepartmentSignal, "department">> = ["productivity", "wellness", "security", "risk"];

export function DepartmentMatrix({ departments }: { departments: DepartmentSignal[] }) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <p className="text-xs uppercase text-cyan">Enterprise Pulse</p>
      <h2 className="mt-2 text-xl font-semibold text-white">Department intelligence matrix</h2>
      <div className="mt-6 overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="border-b border-line pb-3 font-medium">Department</th>
              {rows.map((row) => (
                <th key={row} className="border-b border-line pb-3 font-medium capitalize">
                  {row}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {departments.map((department) => (
              <tr key={department.department} className="border-b border-line/50 last:border-0">
                <td className="py-4 font-medium text-white">{department.department}</td>
                {rows.map((row) => {
                  const value = department[row];
                  const tone = row === "risk" && value > 55 ? "bg-signal" : value > 85 ? "bg-mint" : "bg-cyan";
                  return (
                    <td key={row} className="py-4 pr-4">
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-28 bg-line">
                          <div className={`h-full ${tone}`} style={{ width: `${value}%` }} />
                        </div>
                        <span className="w-8 text-slate-300">{value}</span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
