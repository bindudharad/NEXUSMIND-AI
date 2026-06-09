"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { DashboardForecastPoint } from "@/types/dashboard";

export function ForecastChart({
  series,
  confidence,
}: {
  series: DashboardForecastPoint[];
  confidence: number;
}) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase text-cyan">Prediction Engine</p>
          <h2 className="mt-2 text-xl font-semibold text-white">Revenue, productivity, and risk forecast</h2>
        </div>
        <span className="border border-cyan/30 bg-cyan/10 px-3 py-1 text-sm text-cyan">{confidence}% confidence</span>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={series} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="revenue" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#2EE9D3" stopOpacity={0.38} />
                <stop offset="95%" stopColor="#2EE9D3" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="productivity" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#7CF0A6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#7CF0A6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
            <XAxis dataKey="month" stroke="#64748b" tickLine={false} axisLine={false} />
            <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                background: "#0B1017",
                border: "1px solid #263241",
                color: "#eef7fb",
              }}
            />
            <Area type="monotone" dataKey="revenue" stroke="#2EE9D3" fill="url(#revenue)" strokeWidth={2} />
            <Area type="monotone" dataKey="productivity" stroke="#7CF0A6" fill="url(#productivity)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
