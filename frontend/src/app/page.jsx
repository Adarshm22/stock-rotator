"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    const fetchRow = async () => {
      try {
        const response = await fetch(`${API_URL}/row`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        const payload = await response.json();
        setData(payload);
        setError(null);
        setLastUpdated(new Date());
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
      }
    };

    fetchRow();
    const timerId = setInterval(fetchRow, 60_000);

    return () => clearInterval(timerId);
  }, []);

  const entries = useMemo(() => Object.entries(data?.row ?? {}), [data]);

  return (
    <div className="min-h-screen bg-slate-950">
      <main className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-10 px-6 py-16">
        <header className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              NIFTY CSV Stream
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-100 md:text-4xl">
              Latest Row Snapshot
            </h1>
          </div>
          <div className="flex gap-4 text-sm text-slate-400">
            <span className="rounded-full border border-slate-700 px-3 py-1">
              Updates every 60s
            </span>
            <span className="rounded-full border border-slate-700 px-3 py-1">
              Row {data ? data.index + 1 : "-"} / {data?.total ?? "-"}
            </span>
          </div>
        </header>

        {error && (
          <div className="rounded-xl border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm font-medium text-red-100">
            Unable to load data: {error}
          </div>
        )}

        {!data && !error && (
          <div className="rounded-xl border border-slate-700 bg-slate-900/60 px-4 py-3 text-sm text-slate-200">
            Loading first row...
          </div>
        )}

        {data && (
          <section className="rounded-2xl border border-blue-500/20 bg-slate-900/70 p-6 shadow-[0_20px_40px_rgba(15,23,42,0.35)]">
            <table className="w-full border-collapse text-sm">
              <tbody>
                {entries.map(([key, value]) => (
                  <tr key={key} className="border-b border-slate-700/60 last:border-none">
                    <th className="w-[45%] py-3 text-left font-medium text-slate-400">
                      {key}
                    </th>
                    <td className="py-3 text-left font-semibold text-slate-100">
                      {value}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-4 text-xs text-slate-400">
              Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "-"}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
