import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  Flame,
  Gauge,
  IndianRupee,
  Lock,
  NotebookPen,
  ShieldCheck,
  Target,
  TimerReset,
  TrendingDown,
} from "lucide-react";

const SETUPS = ["Breakout", "Pullback", "Reversal", "Scalp", "News", "No Setup"];
const EMOTIONS = ["Calm", "Confident", "FOMO", "Fear", "Greed", "Revenge"];
const BACKEND = "https://stock-backend-gsyw.onrender.com";
const DEFAULT_RULES = {
  capital: 100000,
  riskPercent: 1,
  maxDailyLoss: 2500,
  maxTrades: 4,
};

function readStorage(key, fallback) {
  try {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : fallback;
  } catch {
    return fallback;
  }
}

function writeStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function currency(value) {
  const number = Number(value || 0);
  return `Rs ${number.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
}

function getDisciplineScore(trades, rules) {
  if (!trades.length) return 100;
  const ruleBreaks = trades.filter((trade) => trade.mistake && trade.mistake !== "None").length;
  const revenge = trades.filter((trade) => trade.emotion === "Revenge" || trade.emotion === "FOMO").length;
  const totalLoss = trades.reduce((sum, trade) => sum + Math.min(Number(trade.pnl || 0), 0), 0);
  const lossPenalty = Math.abs(totalLoss) > Number(rules.maxDailyLoss) ? 25 : 0;
  return Math.max(0, 100 - ruleBreaks * 12 - revenge * 10 - lossPenalty);
}

export default function Coach() {
  const [rules, setRules] = useState(() => readStorage("fintrack-risk-rules", DEFAULT_RULES));
  const [selectedSymbol, setSelectedSymbol] = useState("RELIANCE");
  const [livePrice, setLivePrice] = useState(null);
  const [liveSignals, setLiveSignals] = useState([]);
  const [marketLoading, setMarketLoading] = useState(false);
  const [marketError, setMarketError] = useState("");
  const [entry, setEntry] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [target, setTarget] = useState("");
  const [checklist, setChecklist] = useState({
    setup: false,
    stop: false,
    reward: false,
    emotion: false,
    news: false,
  });
  const [journal, setJournal] = useState(() => readStorage("fintrack-trade-journal", []));
  const [tradeForm, setTradeForm] = useState({
    symbol: "",
    setup: "Breakout",
    emotion: "Calm",
    pnl: "",
    mistake: "None",
    notes: "",
  });

  const selectedSignal = useMemo(() => {
    const clean = selectedSymbol.replace(".NS", "").toUpperCase();
    return liveSignals.find((signal) => {
      const ticker = String(signal?.ticker || signal?.symbol || "").replace(".NS", "").toUpperCase();
      const company = String(signal?.company || "").toUpperCase();
      return ticker === clean || company.includes(clean);
    });
  }, [liveSignals, selectedSymbol]);

  useEffect(() => {
    const loadLiveMarketContext = async () => {
      const clean = selectedSymbol.trim().replace(".NS", "").toUpperCase();
      if (!clean) return;
      setMarketLoading(true);
      setMarketError("");
      try {
        const [stockRes, signalsRes] = await Promise.all([
          fetch(`${BACKEND}/stock?symbol=${encodeURIComponent(clean)}`),
          fetch(`${BACKEND}/signals`),
        ]);
        const stockData = await stockRes.json();
        const signalsData = await signalsRes.json();
        setLivePrice(stockData?.price ? { ...stockData, symbol: clean } : null);
        setLiveSignals(Array.isArray(signalsData?.signals) ? signalsData.signals : []);
      } catch {
        setMarketError("Live market context unavailable right now.");
      } finally {
        setMarketLoading(false);
      }
    };

    loadLiveMarketContext();
    const interval = setInterval(loadLiveMarketContext, 60000);
    return () => clearInterval(interval);
  }, [selectedSymbol]);

  const riskAmount = Number(rules.capital || 0) * (Number(rules.riskPercent || 0) / 100);
  const riskPerShare = Math.abs(Number(entry || 0) - Number(stopLoss || 0));
  const quantity = riskPerShare > 0 ? Math.floor(riskAmount / riskPerShare) : 0;
  const tradeRisk = quantity * riskPerShare;
  const rewardPerShare = Number(target || 0) && Number(entry || 0) ? Math.abs(Number(target) - Number(entry)) : 0;
  const rr = riskPerShare > 0 && rewardPerShare > 0 ? (rewardPerShare / riskPerShare).toFixed(2) : "--";
  const checklistDone = Object.values(checklist).filter(Boolean).length;

  const todayStats = useMemo(() => {
    const today = new Date().toLocaleDateString("en-IN");
    const todayTrades = journal.filter((trade) => trade.date === today);
    const pnl = todayTrades.reduce((sum, trade) => sum + Number(trade.pnl || 0), 0);
    const losses = todayTrades.filter((trade) => Number(trade.pnl || 0) < 0).length;
    const score = getDisciplineScore(todayTrades, rules);
    return { todayTrades, pnl, losses, score };
  }, [journal, rules]);

  const insight = useMemo(() => {
    if (!journal.length) return "Log 3-5 trades and FinTrack will start showing your most expensive habits.";
    const mistakes = journal.filter((trade) => trade.mistake && trade.mistake !== "None");
    const mostCommon = mistakes.reduce((acc, trade) => {
      acc[trade.mistake] = (acc[trade.mistake] || 0) + 1;
      return acc;
    }, {});
    const topMistake = Object.entries(mostCommon).sort((a, b) => b[1] - a[1])[0];
    const bestSetup = Object.entries(
      journal.reduce((acc, trade) => {
        acc[trade.setup] = (acc[trade.setup] || 0) + Number(trade.pnl || 0);
        return acc;
      }, {})
    ).sort((a, b) => b[1] - a[1])[0];

    if (topMistake) return `${topMistake[0]} is your biggest leak. Your best setup by P&L is ${bestSetup?.[0] || "not clear yet"}.`;
    return `Good discipline so far. Your best setup by P&L is ${bestSetup?.[0] || "not clear yet"}.`;
  }, [journal]);

  const updateRules = (nextRules) => {
    setRules(nextRules);
    writeStorage("fintrack-risk-rules", nextRules);
  };

  const saveTrade = () => {
    if (!tradeForm.symbol.trim()) return;
    const nextTrade = {
      ...tradeForm,
      symbol: tradeForm.symbol.trim().toUpperCase(),
      pnl: Number(tradeForm.pnl || 0),
      date: new Date().toLocaleDateString("en-IN"),
      time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    };
    const nextJournal = [nextTrade, ...journal].slice(0, 100);
    setJournal(nextJournal);
    writeStorage("fintrack-trade-journal", nextJournal);
    setTradeForm({ symbol: "", setup: "Breakout", emotion: "Calm", pnl: "", mistake: "None", notes: "" });
  };

  const dailyBlocked =
    todayStats.todayTrades.length >= Number(rules.maxTrades || 0) ||
    todayStats.pnl <= -Math.abs(Number(rules.maxDailyLoss || 0)) ||
    todayStats.losses >= 2;

  return (
    <div className="min-h-screen bg-[#050816] text-white">
      <div className="max-w-7xl mx-auto px-4 md:px-6 py-8">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5 mb-8">
          <div>
            <div className="text-xs text-cyan-400 tracking-widest uppercase mb-2">Trading Discipline OS</div>
            <h1 className="text-3xl md:text-5xl font-bold tracking-tight">Risk Coach</h1>
            <p className="text-gray-400 text-sm md:text-base max-w-2xl mt-3">
              Plan every trade before entry, control position size, stop revenge trading, and learn from every mistake.
            </p>
          </div>
          <div className={`rounded-2xl border px-5 py-4 ${dailyBlocked ? "bg-rose-500/10 border-rose-500/30" : "bg-emerald-500/10 border-emerald-500/25"}`}>
            <div className="flex items-center gap-3">
              {dailyBlocked ? <Lock className="w-5 h-5 text-rose-300" /> : <ShieldCheck className="w-5 h-5 text-emerald-300" />}
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Today Status</p>
                <p className={`font-semibold ${dailyBlocked ? "text-rose-300" : "text-emerald-300"}`}>
                  {dailyBlocked ? "Cooldown Recommended" : "Allowed With Rules"}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <MetricCard icon={Gauge} label="Discipline Score" value={`${todayStats.score}/100`} tone={todayStats.score >= 75 ? "emerald" : todayStats.score >= 50 ? "amber" : "rose"} />
          <MetricCard icon={BarChart3} label="Trades Today" value={`${todayStats.todayTrades.length}/${rules.maxTrades}`} tone="cyan" />
          <MetricCard icon={TrendingDown} label="Daily P&L" value={currency(todayStats.pnl)} tone={todayStats.pnl >= 0 ? "emerald" : "rose"} />
          <MetricCard icon={TimerReset} label="Loss Trades" value={todayStats.losses} tone={todayStats.losses >= 2 ? "rose" : "amber"} />
        </div>

        <section className="mb-6 bg-white/[0.03] border border-white/10 rounded-2xl p-5">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-5 h-5 text-cyan-300" />
                <h2 className="font-semibold">Live Trade Context</h2>
              </div>
              <p className="text-sm text-gray-400 max-w-2xl">
                Pulls current price and signal levels from the live backend. Use it as context, then let the risk calculator decide quantity.
              </p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 lg:min-w-[420px]">
              <TextField label="Symbol" value={selectedSymbol} onChange={setSelectedSymbol} placeholder="RELIANCE" />
              <button
                onClick={() => {
                  if (livePrice?.price) setEntry(String(livePrice.price));
                  if (selectedSignal?.stop_loss) setStopLoss(String(selectedSignal.stop_loss));
                  if (selectedSignal?.target) setTarget(String(selectedSignal.target));
                  if (selectedSymbol) setTradeForm((form) => ({ ...form, symbol: selectedSymbol.toUpperCase() }));
                }}
                disabled={!livePrice?.price && !selectedSignal}
                className="self-end h-[46px] px-4 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/25 text-cyan-200 text-sm font-semibold transition disabled:opacity-40"
              >
                Use Live Levels
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mt-5">
            <OutputCard label="Live Price" value={marketLoading ? "Loading" : livePrice?.price ? currency(livePrice.price) : "Unavailable"} tone="cyan" />
            <OutputCard label="Change" value={livePrice?.percent_change || livePrice?.change || "--"} tone={Number(livePrice?.change || 0) >= 0 ? "emerald" : "rose"} />
            <OutputCard label="Signal" value={selectedSignal?.verdict || "No signal"} tone={selectedSignal?.verdict === "BUY" ? "emerald" : selectedSignal?.verdict === "AVOID" ? "rose" : "amber"} />
            <OutputCard label="Signal Risk" value={selectedSignal?.risk_level || "--"} tone={String(selectedSignal?.risk_level || "").includes("High") ? "rose" : "amber"} />
            <OutputCard label="Setup Score" value={selectedSignal?.setup_score || selectedSignal?.score || "--"} tone="cyan" />
          </div>

          {selectedSignal && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
              <LiveLevel label="Entry Zone" value={selectedSignal.entry_zone ? `${selectedSignal.entry_zone.low} - ${selectedSignal.entry_zone.high}` : "--"} />
              <LiveLevel label="Stop Loss" value={selectedSignal.stop_loss || "--"} />
              <LiveLevel label="Target" value={selectedSignal.target || "--"} />
            </div>
          )}

          {marketError && <p className="text-rose-300 text-xs mt-3">{marketError}</p>}
        </section>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
          <section className="xl:col-span-4 bg-white/[0.03] border border-white/10 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <IndianRupee className="w-5 h-5 text-cyan-300" />
              <h2 className="font-semibold">Position Size Calculator</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <NumberField label="Capital" value={rules.capital} onChange={(value) => updateRules({ ...rules, capital: value })} />
              <NumberField label="Risk %" value={rules.riskPercent} onChange={(value) => updateRules({ ...rules, riskPercent: value })} />
              <NumberField label="Entry" value={entry} onChange={setEntry} />
              <NumberField label="Stop Loss" value={stopLoss} onChange={setStopLoss} />
              <NumberField label="Target" value={target} onChange={setTarget} />
              <div className="rounded-xl bg-cyan-500/10 border border-cyan-500/20 px-3 py-3">
                <p className="text-xs text-gray-400 mb-1">Risk/Reward</p>
                <p className="text-xl font-bold text-cyan-300">{rr}</p>
              </div>
            </div>
            <div className="rounded-2xl bg-black/25 border border-white/10 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Trade Plan Output</p>
              <div className="grid grid-cols-3 gap-3 text-center">
                <Output label="Qty" value={quantity} />
                <Output label="Max Risk" value={currency(tradeRisk)} />
                <Output label="Per Share" value={currency(riskPerShare)} />
              </div>
            </div>
          </section>

          <section className="xl:col-span-4 bg-white/[0.03] border border-white/10 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <ClipboardCheck className="w-5 h-5 text-emerald-300" />
              <h2 className="font-semibold">Pre-Trade Checklist</h2>
            </div>
            <div className="space-y-3">
              {[
                ["setup", "My setup is clearly defined"],
                ["stop", "Stop loss is placed before entry"],
                ["reward", "Risk/reward is at least 1:2"],
                ["emotion", "I am not trading from FOMO or revenge"],
                ["news", "No major news/event risk ignored"],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setChecklist({ ...checklist, [key]: !checklist[key] })}
                  className={`w-full flex items-center gap-3 text-left rounded-xl border px-4 py-3 transition ${
                    checklist[key] ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-200" : "bg-black/20 border-white/10 text-gray-300"
                  }`}
                >
                  <CheckCircle2 className={`w-5 h-5 ${checklist[key] ? "text-emerald-300" : "text-gray-600"}`} />
                  <span className="text-sm">{label}</span>
                </button>
              ))}
            </div>
            <div className={`mt-4 rounded-xl border p-4 ${checklistDone === 5 ? "bg-emerald-500/10 border-emerald-500/25" : "bg-amber-500/10 border-amber-500/20"}`}>
              <p className="text-sm font-semibold">{checklistDone === 5 ? "Trade is rule-ready" : `${5 - checklistDone} rule checks pending`}</p>
              <p className="text-xs text-gray-400 mt-1">This is the pause that saves traders from impulsive entries.</p>
            </div>
          </section>

          <section className="xl:col-span-4 bg-white/[0.03] border border-white/10 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <Flame className="w-5 h-5 text-amber-300" />
              <h2 className="font-semibold">Daily Guardrails</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <NumberField label="Max Daily Loss" value={rules.maxDailyLoss} onChange={(value) => updateRules({ ...rules, maxDailyLoss: value })} />
              <NumberField label="Max Trades" value={rules.maxTrades} onChange={(value) => updateRules({ ...rules, maxTrades: value })} />
            </div>
            <div className="space-y-3">
              <Guardrail active={todayStats.todayTrades.length >= Number(rules.maxTrades)} text="Max trades reached" />
              <Guardrail active={todayStats.pnl <= -Math.abs(Number(rules.maxDailyLoss))} text="Daily loss limit crossed" />
              <Guardrail active={todayStats.losses >= 2} text="Two losses in a day: take cooldown" />
            </div>
            <div className="mt-5 rounded-2xl bg-black/25 border border-white/10 p-4">
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Coach Insight</p>
              <p className="text-sm text-gray-200 leading-6">{insight}</p>
            </div>
          </section>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 mt-6">
          <section className="xl:col-span-4 bg-white/[0.03] border border-white/10 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-5">
              <NotebookPen className="w-5 h-5 text-cyan-300" />
              <h2 className="font-semibold">Fast Trade Journal</h2>
            </div>
            <div className="space-y-3">
              <TextField label="Symbol" value={tradeForm.symbol} onChange={(value) => setTradeForm({ ...tradeForm, symbol: value })} placeholder="RELIANCE" />
              <SelectField label="Setup" value={tradeForm.setup} options={SETUPS} onChange={(value) => setTradeForm({ ...tradeForm, setup: value })} />
              <SelectField label="Emotion" value={tradeForm.emotion} options={EMOTIONS} onChange={(value) => setTradeForm({ ...tradeForm, emotion: value })} />
              <NumberField label="P&L" value={tradeForm.pnl} onChange={(value) => setTradeForm({ ...tradeForm, pnl: value })} />
              <TextField label="Mistake" value={tradeForm.mistake} onChange={(value) => setTradeForm({ ...tradeForm, mistake: value })} placeholder="None / Late entry / No SL" />
              <textarea
                value={tradeForm.notes}
                onChange={(event) => setTradeForm({ ...tradeForm, notes: event.target.value })}
                placeholder="What happened?"
                className="w-full min-h-24 bg-black/25 border border-white/10 rounded-xl px-3 py-3 text-sm outline-none focus:border-cyan-400/40 placeholder-gray-600"
              />
              <button onClick={saveTrade} className="w-full bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/25 text-cyan-200 rounded-xl py-3 text-sm font-semibold transition">
                Save Trade
              </button>
            </div>
          </section>

          <section className="xl:col-span-8 bg-white/[0.03] border border-white/10 rounded-2xl overflow-hidden">
            <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
              <div>
                <h2 className="font-semibold">Recent Trades</h2>
                <p className="text-xs text-gray-500 mt-1">Your data is saved locally in this browser.</p>
              </div>
              <Target className="w-5 h-5 text-cyan-300" />
            </div>
            {journal.length === 0 ? (
              <div className="py-16 text-center text-gray-500">
                <NotebookPen className="w-10 h-10 mx-auto mb-3 opacity-50" />
                <p>No trades logged yet</p>
                <p className="text-xs mt-1">Start logging today to see mistake patterns.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      {["Time", "Symbol", "Setup", "Emotion", "P&L", "Mistake", "Notes"].map((heading) => (
                        <th key={heading} className="px-4 py-3 text-left text-xs text-gray-500 uppercase tracking-wider whitespace-nowrap">{heading}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {journal.slice(0, 12).map((trade, index) => (
                      <tr key={`${trade.symbol}-${trade.time}-${index}`} className="border-b border-white/5 hover:bg-white/[0.03]">
                        <td className="px-4 py-4 text-xs text-gray-500 whitespace-nowrap">{trade.date} {trade.time}</td>
                        <td className="px-4 py-4 font-semibold">{trade.symbol}</td>
                        <td className="px-4 py-4 text-sm text-gray-300">{trade.setup}</td>
                        <td className="px-4 py-4 text-sm text-gray-300">{trade.emotion}</td>
                        <td className={`px-4 py-4 font-semibold ${Number(trade.pnl) >= 0 ? "text-emerald-400" : "text-rose-400"}`}>{currency(trade.pnl)}</td>
                        <td className="px-4 py-4 text-sm text-gray-300">{trade.mistake}</td>
                        <td className="px-4 py-4 text-sm text-gray-500 max-w-xs truncate">{trade.notes || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>

        <div className="mt-6 flex items-start gap-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 p-4 text-sm text-amber-100">
          <AlertTriangle className="w-5 h-5 text-amber-300 shrink-0 mt-0.5" />
          <p>Educational tool only. FinTrack helps with discipline and risk planning, but it does not guarantee profit or replace financial advice.</p>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, tone }) {
  const tones = {
    emerald: "text-emerald-300 border-emerald-500/20 bg-emerald-500/10",
    amber: "text-amber-300 border-amber-500/20 bg-amber-500/10",
    rose: "text-rose-300 border-rose-500/20 bg-rose-500/10",
    cyan: "text-cyan-300 border-cyan-500/20 bg-cyan-500/10",
  };
  return (
    <div className={`rounded-2xl border p-4 ${tones[tone] || tones.cyan}`}>
      <div className="flex items-center gap-2 text-gray-300 mb-3">
        <Icon className="w-4 h-4" />
        <p className="text-xs uppercase tracking-wider">{label}</p>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function NumberField({ label, value, onChange }) {
  return (
    <label className="block">
      <span className="text-xs text-gray-500 mb-1 block">{label}</span>
      <input
        type="number"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full bg-black/25 border border-white/10 rounded-xl px-3 py-3 text-sm outline-none focus:border-cyan-400/40"
      />
    </label>
  );
}

function TextField({ label, value, onChange, placeholder }) {
  return (
    <label className="block">
      <span className="text-xs text-gray-500 mb-1 block">{label}</span>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className="w-full bg-black/25 border border-white/10 rounded-xl px-3 py-3 text-sm outline-none focus:border-cyan-400/40 placeholder-gray-600"
      />
    </label>
  );
}

function SelectField({ label, value, options, onChange }) {
  return (
    <label className="block">
      <span className="text-xs text-gray-500 mb-1 block">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full bg-black/25 border border-white/10 rounded-xl px-3 py-3 text-sm outline-none focus:border-cyan-400/40"
      >
        {options.map((option) => (
          <option key={option} value={option} className="bg-[#050816]">
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function Output({ label, value }) {
  return (
    <div>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function OutputCard({ label, value, tone }) {
  const tones = {
    emerald: "border-emerald-500/20 bg-emerald-500/10 text-emerald-300",
    amber: "border-amber-500/20 bg-amber-500/10 text-amber-300",
    rose: "border-rose-500/20 bg-rose-500/10 text-rose-300",
    cyan: "border-cyan-500/20 bg-cyan-500/10 text-cyan-300",
  };
  return (
    <div className={`rounded-xl border px-3 py-3 ${tones[tone] || tones.cyan}`}>
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="text-base font-semibold text-white">{value}</p>
    </div>
  );
}

function LiveLevel({ label, value }) {
  return (
    <div className="rounded-xl bg-black/25 border border-white/10 px-4 py-3">
      <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-sm text-gray-200">{value}</p>
    </div>
  );
}

function Guardrail({ active, text }) {
  return (
    <div className={`flex items-center gap-3 rounded-xl border px-3 py-3 ${active ? "bg-rose-500/10 border-rose-500/25 text-rose-200" : "bg-emerald-500/10 border-emerald-500/20 text-emerald-200"}`}>
      {active ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
      <p className="text-sm">{text}</p>
    </div>
  );
}
