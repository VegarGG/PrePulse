"use client";

import type { PostureGrade } from "@/lib/types";

function bandColor(score: number): string {
  if (score >= 90) return "#10b981"; // emerald
  if (score >= 75) return "#22c55e"; // green
  if (score >= 60) return "#eab308"; // yellow
  if (score >= 40) return "#f97316"; // orange
  return "#ef4444"; // red
}

export function PostureGauge({
  score,
  grade,
  label = "Posture",
}: {
  score: number | null;
  grade: PostureGrade | null;
  label?: string;
}) {
  const value = score ?? 0;
  const color = bandColor(value);

  // Gauge geometry (all in SVG units, y increases downward).
  // Arc endpoints sit on the chord at y=baseY, apex at y=baseY-radius.
  const width = 260;
  const height = 150;
  const cx = width / 2;
  const baseY = 120;
  const radius = 95;
  const strokeWidth = 18;

  const leftX = cx - radius;
  const rightX = cx + radius;

  // sweep-flag=1 with y-down SVG produces a dome (arc bulges to smaller y).
  const arcPath = `M ${leftX} ${baseY} A ${radius} ${radius} 0 0 1 ${rightX} ${baseY}`;

  const circumference = Math.PI * radius;
  const filled = (value / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-2">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        {/* Track */}
        <path
          d={arcPath}
          stroke="hsl(var(--muted))"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
        />
        {/* Fill */}
        <path
          d={arcPath}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          style={{
            transition: "stroke-dasharray 600ms ease-out, stroke 600ms ease-out",
          }}
        />
        {/* Score number */}
        <text
          x={cx}
          y={baseY - 28}
          textAnchor="middle"
          className="fill-foreground"
          style={{ fontSize: 44, fontWeight: 700 }}
        >
          {score === null ? "—" : value}
        </text>
        {/* Label under the number, still inside the dome */}
        <text
          x={cx}
          y={baseY - 8}
          textAnchor="middle"
          className="fill-muted-foreground"
          style={{ fontSize: 11, letterSpacing: 2 }}
        >
          {label.toUpperCase()}
        </text>
      </svg>
      {grade && (
        <div className="mt-1 text-sm" style={{ color }}>
          Grade <span className="font-bold text-lg">{grade}</span>
        </div>
      )}
    </div>
  );
}
