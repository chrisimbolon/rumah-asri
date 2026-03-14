"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { DataGrafik } from "@/lib/mock-data";

interface Props {
  data: DataGrafik[];
}

export default function SalesChart({ data }: Props) {
  const max = Math.max(...data.map((d) => d.penjualan));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart
        data={data}
        barSize={28}
        margin={{ top: 4, right: 4, left: -24, bottom: 0 }}
      >
        <XAxis
          dataKey="bulan"
          tick={{ fontSize: 11, fill: "var(--color-ink-3)" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--color-ink-3)" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "white",
            border: "1px solid rgba(14,13,11,0.10)",
            borderRadius: 4,
            fontSize: 12,
            padding: "6px 12px",
            boxShadow: "0 4px 20px rgba(14,13,11,0.09)",
          }}
          formatter={(v: number) => [`${v} unit`, "Penjualan"]}
          cursor={{ fill: "rgba(14,13,11,0.04)" }}
        />
        <Bar dataKey="penjualan" radius={[3, 3, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={i}
              fill={
                entry.penjualan === max
                  ? "var(--color-accent)"
                  : "#D4DCEF"
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
