"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const HISTORY_STORAGE_KEY = "stock-rotator-history-v1";
const ALERT_STORAGE_KEY = "stock-rotator-alerts-v1";
const MAX_HISTORY_MESSAGES = 50; // Keep only last 50 messages

const formatTime = (value) => {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

export default function Home() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [chatError, setChatError] = useState(null);
  const [conditions, setConditions] = useState([]);
  const [alertShownById, setAlertShownById] = useState({});
  const [latestAlert, setLatestAlert] = useState(null);

  // Debug: Log when messages change
  useEffect(() => {
    console.log("Messages state changed. Count:", messages.length);
  }, [messages]);

  useEffect(() => {
    const storedAlerts = localStorage.getItem(ALERT_STORAGE_KEY);
    if (storedAlerts) {
      try {
        setAlertShownById(JSON.parse(storedAlerts));
      } catch {
        setAlertShownById({});
      }
    }
    const storedMessages = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (storedMessages) {
      try {
        const parsed = JSON.parse(storedMessages);
        console.log("Loaded messages from localStorage:", parsed.length);
        setMessages(parsed);
      } catch (err) {
        console.error("Failed to load messages:", err);
        setMessages([]);
      }
    }

    // Reload messages when tab becomes visible again (prevents loss on browser sleep)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        const currentMessages = localStorage.getItem(HISTORY_STORAGE_KEY);
        if (currentMessages) {
          try {
            const parsed = JSON.parse(currentMessages);
            setMessages((prev) => {
              // Only update if localStorage has more messages
              if (parsed.length > prev.length) {
                console.log("Reloaded messages on visibility change:", parsed.length);
                return parsed;
              }
              return prev;
            });
          } catch (err) {
            console.error("Failed to reload messages on visibility change:", err);
          }
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      try {
        // Keep only last MAX_HISTORY_MESSAGES messages
        const messagesToSave = messages.slice(-MAX_HISTORY_MESSAGES);
        console.log("Saving messages to localStorage:", messagesToSave.length);
        localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(messagesToSave));
      } catch (err) {
        console.error("Failed to save messages:", err);
        // If localStorage is full, clear old data and try again
        if (err.name === 'QuotaExceededError') {
          console.log("Storage full, keeping only last 20 messages");
          const recentMessages = messages.slice(-20);
          localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(recentMessages));
        }
      }
    }
  }, [messages]);

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
        console.error("Fetch row error:", err);
      }
    };

    fetchRow();
    const timerId = setInterval(fetchRow, 60_000);

    return () => clearInterval(timerId);
  }, []);

  useEffect(() => {
    const fetchConditions = async () => {
      try {
        const response = await fetch(`${API_URL}/conditions`, { cache: "no-store" });
        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }
        const payload = await response.json();
        // Backend returns array directly, not wrapped in object
        setConditions(Array.isArray(payload) ? payload : []);
      } catch (err) {
        console.error("Fetch conditions error:", err);
        // Don't reset conditions on error to preserve existing data
      }
    };

    fetchConditions();
    const timerId = setInterval(fetchConditions, 15_000);
    return () => clearInterval(timerId);
  }, []);

  useEffect(() => {
    if (!conditions.length) return;
    const newlyTriggered = {};
    conditions.forEach((condition) => {
      if (condition.status === "triggered" && !alertShownById[condition.id]) {
        newlyTriggered[condition.id] = new Date().toISOString();
        setLatestAlert({
          id: condition.id,
          message: condition.message,
          time: new Date().toISOString(),
        });
      }
    });
    if (Object.keys(newlyTriggered).length) {
      setAlertShownById((prev) => {
        const next = { ...prev, ...newlyTriggered };
        localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    }
  }, [conditions, alertShownById]);

  const entries = useMemo(() => Object.entries(data?.row ?? {}), [data]);

  const history = useMemo(
    () =>
      conditions.map((condition) => ({
        ...condition,
        alert_shown_time: alertShownById[condition.id] ?? null,
      })),
    [conditions, alertShownById]
  );

  const handleSend = async () => {
    if (!input.trim()) return;
    const commandTime = new Date().toISOString();
    const userMessage = {
      role: "user",
      content: input.trim(),
      time: commandTime,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setChatError(null);

    try {
      console.log("Sending to:", `${API_URL}/chat`);
      console.log("Payload:", { message: userMessage.content, command_time: commandTime });
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
      
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage.content, command_time: commandTime }),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      console.log("Response status:", response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Request failed: ${response.status}`);
      }
      const payload = await response.json();
      console.log("Success payload:", payload);
      
      const assistantMessage = {
        role: "assistant",
        content: payload.assistant_message,
        time: payload.parsed_time,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setConditions((prev) => [payload, ...prev]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to send message";
      console.error("Chat error:", err);
      setChatError(message);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-400">
              NIFTY CSV Stream
            </p>
            <h1 className="mt-2 text-3xl font-semibold md:text-4xl">
              Stock Rotator Command Center
            </h1>
          </div>
          <div className="flex flex-wrap gap-3 text-sm text-slate-400">
            <span className="rounded-full border border-slate-700 px-3 py-1">
              Updates every 60s
            </span>
            <span className="rounded-full border border-slate-700 px-3 py-1">
              Row {data ? data.index + 1 : "-"} / {data?.total ?? "-"}
            </span>
          </div>
        </header>

        {latestAlert && (
          <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm font-medium text-emerald-100">
            Alert triggered: {latestAlert.message} ({formatTime(latestAlert.time)})
          </div>
        )}

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
          <section className="rounded-2xl border border-blue-500/20 bg-slate-900/70 p-4 shadow-[0_20px_40px_rgba(15,23,42,0.35)]">
            <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-3 text-xs text-slate-400">
              <span>Current CSV row attributes</span>
              <span>Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "-"}</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              {entries.map(([key, value]) => (
                <div
                  key={key}
                  className="min-w-[170px] flex-1 rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2"
                >
                  <div className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                    {key}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-slate-100">
                    {value}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Trading Assistant</h2>
              <span className="text-xs text-slate-400">Gemini 2.5 Flash</span>
            </div>
            <div className="mt-4 h-[360px] overflow-y-auto rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm">
              {messages.length === 0 && (
                <div className="text-slate-500">
                  Ask the bot to watch a condition from the CSV data.
                </div>
              )}
              <div className="flex flex-col gap-4">
                {messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`rounded-xl px-3 py-2 ${
                      message.role === "user"
                        ? "bg-blue-500/15 text-blue-100"
                        : "bg-slate-800 text-slate-100"
                    }`}
                  >
                    <div className="text-xs uppercase tracking-[0.2em] text-slate-400">
                      {message.role}
                    </div>
                    <div className="mt-1 whitespace-pre-wrap">{message.content}</div>
                    <div className="mt-1 text-[11px] text-slate-500">
                      {formatTime(message.time)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            {chatError && (
              <div className="mt-3 rounded-lg border border-red-500/50 bg-red-500/10 px-3 py-2 text-xs text-red-100">
                {chatError}
              </div>
            )}
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Example: Alert me when CLOSE is above 25000"
                className="flex-1 rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none focus:border-blue-500"
              />
              <button
                onClick={handleSend}
                className="rounded-xl bg-blue-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-600"
              >
                Send
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <h2 className="text-lg font-semibold">Execution History</h2>
            <p className="mt-1 text-xs text-slate-400">
              Command time, condition parsed time, and alert shown time.
            </p>
            <div className="mt-4 space-y-4">
              {history.length === 0 && (
                <div className="rounded-xl border border-slate-800 bg-slate-950/50 px-3 py-4 text-xs text-slate-500">
                  No trades or alerts yet.
                </div>
              )}
              {history.map((item) => (
                <div key={item.id} className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-3 text-xs">
                  <div className="text-sm font-semibold text-slate-100">
                    {item.message}
                  </div>
                  <div className="mt-2 grid gap-2 text-slate-300">
                    <div>
                      <span className="font-semibold text-slate-400">Command:</span>{" "}
                      {formatTime(item.command_time)}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-400">Condition parsed:</span>{" "}
                      {formatTime(item.parsed_time)}
                    </div>
                    <div>
                      <span className="font-semibold text-slate-400">Alert shown:</span>{" "}
                      {formatTime(item.alert_shown_time)}
                    </div>
                  </div>
                  <div className="mt-2 text-[11px] uppercase tracking-[0.2em] text-slate-500">
                    Status: {item.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
