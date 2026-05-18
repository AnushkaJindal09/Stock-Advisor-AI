import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

const BACKEND = "https://stock-backend-gsyw.onrender.com";

// ─── Confluence grade ───
function getConfluenceGrade(s) {
  let score = 0;
  if (s.signals?.macd === "Bullish") score++;
  if (s.signals?.trend?.includes("Uptrend")) score++;
  if (s.signals?.rsi >= 40 && s.signals?.rsi <= 65) score++;
  if (s.volume_ratio >= 1.5) score++;
  if (s.multi_timeframe?.["1h"] === "Bullish") score++;
  if (s.multi_timeframe?.["1d"] === "Bullish") score++;
  if (score >= 5) return { grade: "A+", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" };
  if (score >= 4) return { grade: "A",  color: "text-emerald-300", bg: "bg-emerald-500/10 border-emerald-500/20" };
  if (score >= 3) return { grade: "B",  color: "text-amber-300",   bg: "bg-amber-500/10  border-amber-500/20"   };
  if (score >= 2) return { grade: "C",  color: "text-rose-300",    bg: "bg-rose-500/10   border-rose-500/20"    };
  return           { grade: "D",  color: "text-gray-500",    bg: "bg-white/5       border-white/10"     };
}

// ─── Why NOT to trade ───
function getWhyNot(s) {
  const reasons = [];
  if (s.signals?.rsi > 68)
    reasons.push("RSI overbought zone mein hai — entry risky hai.");
  if (s.signals?.macd === "Bearish")
    reasons.push("MACD bearish hai — momentum weak.");
  if (s.risk_level === "High")
    reasons.push("High risk setup — position size chhota rakhein.");
  if (s.volume_ratio < 0.8)
    reasons.push("Volume bahut kam hai — conviction nahi dikh rahi.");
  if (s.multi_timeframe?.["1d"] === "Bearish")
    reasons.push("Daily timeframe bearish hai — overall trend against.");
  if (s.signals?.trend?.includes("Downtrend"))
    reasons.push("Strong downtrend mein entry avoid karein.");
  if (s.percent_change < -3)
    reasons.push(`Aaj ${s.percent_change}% gira — panic selling possible.`);
  if (reasons.length === 0)
    reasons.push("Koi major red flag nahi — but confirmation ka wait karein.");
  return reasons;
}

// ─────────────────────────────────────────
function Markets() {
  const [signals, setSignals]           = useState([]);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState(null);
  const [lastUpdated, setLastUpdated]   = useState("");
  const [menuOpen, setMenuOpen]         = useState(false);
  const [search, setSearch]             = useState("");
  const [nifty, setNifty]               = useState(null);
  const [niftyLoading, setNiftyLoading] = useState(true);
  const [filter, setFilter]             = useState("ALL");

  useEffect(() => {
    fetchSignals();
    fetchNifty();
  }, []);

  const fetchNifty = async () => {
    try {
      setNiftyLoading(true);
      const res  = await fetch(`${BACKEND}/stock?symbol=NIFTY50`);
      const data = await res.json();
      setNifty(data);
    } catch {
      setNifty(null);
    } finally {
      setNiftyLoading(false);
    }
  };

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);
      const res  = await fetch(`${BACKEND}/signals`);
      const data = await res.json();
      setSignals(data.signals || []);
      setLastUpdated(data.generated_at || "");
    } catch {
      setError("Failed to load market signals.");
    } finally {
      setLoading(false);
    }
  };

  const filteredSignals = useMemo(() => {
    return signals
      .filter((s) => s.company?.toLowerCase().includes(search.toLowerCase()))
      .filter((s) => filter === "ALL" || s.verdict === filter);
  }, [signals, search, filter]);

  const buySignals   = signals.filter((s) => s.verdict === "BUY");
  const waitSignals  = signals.filter((s) => s.verdict === "WAIT");
  const avoidSignals = signals.filter((s) => s.verdict === "AVOID");

  const bestSetup = useMemo(() => {
    const buys = signals.filter((s) => s.verdict === "BUY");
    if (buys.length > 0) return buys[0];
    const sorted = [...signals].sort((a, b) => (b.technical_strength || 0) - (a.technical_strength || 0));
    return sorted[0] || null;
  }, [signals]);

  const marketMood =
    buySignals.length > avoidSignals.length ? "Bullish"
    : avoidSignals.length > buySignals.length ? "Bearish"
    : "Neutral";

  const niftyUp = nifty?.change >= 0;

  const getScoreColor   = (sc) => sc >= 65 ? "text-emerald-400" : sc >= 40 ? "text-amber-300" : "text-rose-400";
  const getVerdictStyle = (v)  =>
    v === "BUY"   ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" :
    v === "AVOID" ? "bg-rose-500/10 text-rose-300 border-rose-500/30" :
                    "bg-amber-500/10 text-amber-300 border-amber-500/30";
  const getRiskStyle = (r) =>
    r?.includes("Low") ? "text-emerald-300" : r?.includes("High") ? "text-rose-300" : "text-amber-300";

  return (
    <div className="min-h-screen bg-[#050816] text-white">

      {/* NAV */}


      <div className="max-w-5xl mx-auto px-4 md:px-6 py-10">

        {/* ── NIFTY50 CONTEXT BANNER ── */}
        <div className={`rounded-2xl border px-5 py-4 mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4
          ${niftyLoading ? "bg-white/[0.02] border-white/8"
            : niftyUp    ? "bg-emerald-500/[0.05] border-emerald-500/20"
                         : "bg-rose-500/[0.05] border-rose-500/20"}`}
        >
          <div>
            <p className="text-gray-500 text-[10px] uppercase tracking-widest mb-1">Market Context — Nifty 50</p>
            {niftyLoading ? (
              <p className="text-gray-400 text-sm">Fetching Nifty data...</p>
            ) : nifty?.error ? (
              <p className="text-gray-500 text-sm">Nifty data unavailable</p>
            ) : (
              <>
                <div className="flex items-baseline gap-3">
                  <span className="text-white text-2xl font-bold">₹{nifty?.price?.toLocaleString()}</span>
                  <span className={`text-sm font-semibold ${niftyUp ? "text-emerald-400" : "text-rose-400"}`}>
                    {niftyUp ? "+" : ""}{nifty?.change?.toFixed(2)} ({nifty?.percent_change})
                  </span>
                </div>
                <p className="text-gray-400 text-xs mt-1 max-w-xl">
                  {niftyUp
                    ? "Overall market bullish hai — individual BUY setups zyada reliable honge aaj."
                    : "Overall market weak hai — experts aaj fresh entries se bachenge, sirf A+ setups consider karenge."}
                </p>
              </>
            )}
          </div>
          <div className="shrink-0">
            <div className={`text-xs font-semibold px-3 py-1.5 rounded-full border
              ${niftyLoading ? "text-gray-500 border-white/10 bg-white/5"
                : niftyUp   ? "text-emerald-300 border-emerald-500/30 bg-emerald-500/10"
                            : "text-rose-300 border-rose-500/30 bg-rose-500/10"}`}>
              {niftyLoading ? "Loading..." : niftyUp ? "📈 Market Bullish" : "📉 Market Weak"}
            </div>
          </div>
        </div>

        {/* HEADER */}
        <div className="flex flex-col xl:flex-row xl:items-end xl:justify-between gap-6 mb-10">
          <div>
            <p className="text-cyan-400 text-xs font-semibold tracking-widest uppercase mb-3">Live AI Market Signals</p>
            <h1 className="text-4xl md:text-5xl font-bold leading-tight">Smart Markets Dashboard</h1>
            <p className="text-gray-400 mt-4 max-w-2xl leading-7 text-sm">
              Real-time technical analysis with AI-powered signals, expert psychology, confluence grading and risk management.
            </p>
            <p className="text-xs text-gray-600 mt-3">Last Updated: {lastUpdated || "Loading..."}</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="Search company..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm outline-none focus:border-cyan-400/40 w-full sm:w-[220px] placeholder-gray-600"
            />
            <button
              onClick={() => { fetchSignals(); fetchNifty(); }}
              className="bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-300 px-5 py-3 rounded-xl text-sm font-medium transition"
            >
              Refresh
            </button>
          </div>
        </div>

        {/* SUMMARY CARDS */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-8">
          <SummaryCard title="BUY"     value={buySignals.length}   color="emerald" />
          <SummaryCard title="WAIT"    value={waitSignals.length}  color="amber"   />
          <SummaryCard title="AVOID"   value={avoidSignals.length} color="rose"    />
          <SummaryCard title="TRACKED" value={signals.length}      color="cyan"    />
        </div>

        {/* MARKET MOOD */}
        <div className="bg-white/[0.02] border border-white/8 rounded-2xl px-6 py-5 mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <p className="text-cyan-300 font-semibold text-sm mb-1">AI Market Sentiment</p>
            <p className="text-gray-400 text-sm leading-6 max-w-2xl">
              {marketMood === "Bullish"
                ? "Momentum positive dikh raha hai. Multiple stocks strength show kar rahe hain aur bullish continuation possible hai."
                : marketMood === "Bearish"
                ? "Market weak zone mein hai. Experts fresh entries avoid karenge jab tak confirmation aur strength return nahi hoti."
                : "Market mixed signals de raha hai. High probability setups ka patiently wait karna better rahega."}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className="text-gray-500 text-xs mb-1">Overall Mood</p>
            <div className={`text-2xl font-bold ${marketMood === "Bullish" ? "text-emerald-400" : marketMood === "Bearish" ? "text-rose-400" : "text-amber-300"}`}>
              {marketMood}
            </div>
          </div>
        </div>

        {/* ── BEST SETUP OF THE DAY ── */}
        {!loading && bestSetup && (
          <div className="mb-10">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-amber-300">⭐</span>
              <p className="text-amber-300 text-xs font-semibold uppercase tracking-widest">Best Setup of the Day</p>
              <span className="text-gray-600 text-xs">— Expert's top pick from all tracked stocks</span>
            </div>
            <div className="bg-amber-500/[0.04] border border-amber-500/20 rounded-2xl p-5">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-5">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <h2 className="text-xl font-bold text-white">{bestSetup.company}</h2>
                    {bestSetup.sector && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/8 text-gray-400">{bestSetup.sector}</span>
                    )}
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${getConfluenceGrade(bestSetup).bg} ${getConfluenceGrade(bestSetup).color}`}>
                      {getConfluenceGrade(bestSetup).grade} Confluence
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2 mt-2">
                    <span className="text-2xl font-bold text-white">₹{bestSetup.price?.toLocaleString()}</span>
                    <span className={`text-sm ${bestSetup.percent_change >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {bestSetup.percent_change >= 0 ? "+" : ""}{bestSetup.percent_change}%
                    </span>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getVerdictStyle(bestSetup.verdict)}`}>
                    {bestSetup.verdict}
                  </span>
                  <div className={`text-3xl font-bold mt-2 ${getScoreColor(bestSetup.setup_score)}`}>
                    {bestSetup.setup_score}
                  </div>
                  <p className="text-gray-600 text-[10px] uppercase tracking-wider">Confidence</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-white/[0.03] border border-white/5 rounded-xl p-3">
                  <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">Entry Zone</p>
                  <p className="text-cyan-300 text-xs font-medium">₹{bestSetup.entry_zone?.low} – ₹{bestSetup.entry_zone?.high}</p>
                </div>
                <div className="bg-rose-500/[0.06] border border-rose-500/10 rounded-xl p-3">
                  <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">Stop Loss</p>
                  <p className="text-rose-300 text-xs font-medium">₹{bestSetup.stop_loss?.toLocaleString()}</p>
                </div>
                <div className="bg-emerald-500/[0.06] border border-emerald-500/10 rounded-xl p-3">
                  <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-1">Target</p>
                  <p className="text-emerald-300 text-xs font-medium">₹{bestSetup.target?.toLocaleString()}</p>
                </div>
              </div>
              {bestSetup.why?.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-gray-500 text-[10px] uppercase tracking-wider mb-2">Why this is today's best setup</p>
                  {bestSetup.why.slice(0, 2).map((r, i) => (
                    <p key={i} className="text-gray-300 text-xs leading-5">· {r}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* LOADING */}
        {loading && (
          <div className="py-24 flex flex-col items-center">
            <div className="w-10 h-10 rounded-full border-4 border-cyan-400 border-t-transparent animate-spin mb-5"></div>
            <p className="text-gray-500 text-sm">Fetching live market signals...</p>
          </div>
        )}

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-5 text-rose-300 text-center text-sm">
            {error}
          </div>
        )}

        {/* ── SIGNALS LIST ── */}
        {!loading && !error && (
          <>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-5">
              <h2 className="text-xl font-semibold">All Stock Signals</h2>
              <div className="flex items-center gap-2 flex-wrap">
                {["ALL", "BUY", "WAIT", "AVOID"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition
                      ${filter === f
                        ? f === "BUY"   ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                        : f === "AVOID" ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                        : f === "WAIT"  ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                        :                 "bg-white/10 text-white border-white/20"
                        : "bg-white/[0.02] text-gray-500 border-white/8 hover:text-gray-300"
                      }`}
                  >
                    {f}
                  </button>
                ))}
                <span className="text-gray-600 text-xs">{filteredSignals.length} stocks</span>
              </div>
            </div>

            <div className="flex flex-col gap-4">
              {filteredSignals.map((s) => (
                <SignalCard
                  key={s.ticker}
                  s={s}
                  getScoreColor={getScoreColor}
                  getVerdictStyle={getVerdictStyle}
                  getRiskStyle={getRiskStyle}
                  isBestSetup={s.ticker === bestSetup?.ticker}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ─── Summary Card ─── */
function SummaryCard({ title, value, color }) {
  const colors = {
    emerald: "text-emerald-400 border-emerald-500/10",
    amber:   "text-amber-300  border-amber-500/10",
    rose:    "text-rose-400   border-rose-500/10",
    cyan:    "text-cyan-400   border-cyan-500/10",
  };
  return (
    <div className={`bg-white/[0.03] border rounded-2xl p-5 ${colors[color]}`}>
      <p className="text-gray-500 text-xs tracking-widest uppercase">{title}</p>
      <h2 className="text-4xl font-bold mt-3">{value}</h2>
    </div>
  );
}

/* ─── Mini Sparkline ─── */
function MiniChart({ data = [] }) {
  if (!data?.length) return null;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100;
    const y = 38 - ((d - min) / (max - min || 1)) * 34;
    return `${x},${y}`;
  }).join(" ");
  const isUp = data[data.length - 1] >= data[0];
  return (
    <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="w-full h-12">
      <polyline fill="none" stroke={isUp ? "#34d399" : "#f87171"} strokeWidth="1.8" points={points} />
    </svg>
  );
}

/* ─── Signal Card ─── */
function SignalCard({ s, getScoreColor, getVerdictStyle, getRiskStyle, isBestSetup }) {
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab]           = useState("why");

  const riskReward =
    s.risk_reward != null ? s.risk_reward
    : s.target && s.stop_loss && s.price
    ? (Math.abs(s.target - s.price) / Math.abs(s.price - s.stop_loss)).toFixed(1)
    : "--";

  const upside =
    s.upside_percent != null ? s.upside_percent
    : s.target && s.price ? (((s.target - s.price) / s.price) * 100).toFixed(1)
    : "--";

  const downside =
    s.downside_percent != null ? s.downside_percent
    : s.stop_loss && s.price ? (((s.price - s.stop_loss) / s.price) * 100).toFixed(1)
    : "--";

  const volumeRatio = s.volume_ratio != null ? s.volume_ratio : "--";
  const confluence  = getConfluenceGrade(s);
  const whyNot      = getWhyNot(s);

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className={`border rounded-2xl cursor-pointer transition-all duration-300
        ${isBestSetup
          ? "bg-amber-500/[0.03] border-amber-500/20 hover:border-amber-500/40"
          : `bg-[#0b1120] hover:border-white/20 ${expanded ? "border-cyan-500/25" : "border-white/8"}`}
      `}
    >
      {/* ── TOP ── */}
      <div className="px-6 pt-5 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <h2 className="text-lg font-semibold text-white tracking-tight">{s.company}</h2>
              {s.sector && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 border border-white/8 text-gray-400">{s.sector}</span>
              )}
              <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${confluence.bg} ${confluence.color}`}>
                {confluence.grade}
              </span>
              {isBestSetup && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300">⭐ Best Setup</span>
              )}
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-bold text-white">₹{s.price?.toLocaleString()}</span>
              {s.percent_change !== undefined && (
                <span className={`text-sm font-medium ${s.percent_change >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {s.percent_change >= 0 ? "+" : ""}{s.percent_change}%
                </span>
              )}
            </div>
          </div>
          <div className="text-right shrink-0">
            <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getVerdictStyle(s.verdict)}`}>
              {s.verdict}
            </span>
            <div className={`text-3xl font-bold mt-3 ${getScoreColor(s.setup_score)}`}>{s.setup_score || "--"}</div>
            <p className="text-gray-600 text-[10px] mt-0.5 uppercase tracking-wider">Confidence</p>
          </div>
        </div>

        {s.mini_chart?.length > 0 && (
          <div className="mt-3 -mx-1"><MiniChart data={s.mini_chart} /></div>
        )}

        {s.alerts?.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {s.alerts.map((alert, i) => (
              <span key={i} className="px-2 py-0.5 rounded-full text-[10px] bg-amber-500/10 border border-amber-500/20 text-amber-300">{alert}</span>
            ))}
          </div>
        )}
      </div>

      {/* ── 3 COLUMNS ── */}
      <div className="border-t border-white/5 px-6 py-4 grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Technical */}
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
          <p className="text-cyan-400 text-[10px] font-semibold uppercase tracking-widest mb-4">Technical Signal</p>
          <div className="space-y-3">
            {[
              { label: "RSI",    val: s.signals?.rsi   || "--" },
              { label: "MACD",   val: s.signals?.macd  || "--" },
              { label: "Trend",  val: s.signals?.trend || "--" },
              { label: "Volume", val: volumeRatio !== "--" ? `${volumeRatio}x` : "--" },
            ].map((row) => (
              <div key={row.label} className="flex items-center justify-between">
                <p className="text-gray-500 text-[11px] uppercase tracking-wider">{row.label}</p>
                <p className="text-white text-sm font-medium">{row.val}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Execution */}
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
          <p className="text-cyan-400 text-[10px] font-semibold uppercase tracking-widest mb-4">Execution Plan</p>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-gray-500 text-[11px] uppercase tracking-wider">Entry</p>
              <p className="text-cyan-300 text-sm font-medium">₹{s.entry_zone?.low || s.price} – ₹{s.entry_zone?.high || s.price}</p>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-gray-500 text-[11px] uppercase tracking-wider">Target</p>
              <p className="text-emerald-300 text-sm font-medium">
                ₹{s.target?.toLocaleString() || "--"}
                {upside !== "--" && <span className="text-emerald-400/60 text-[10px] ml-1">(↑{upside}%)</span>}
              </p>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-gray-500 text-[11px] uppercase tracking-wider">Stop Loss</p>
              <p className="text-rose-300 text-sm font-medium">
                ₹{s.stop_loss?.toLocaleString() || "--"}
                {downside !== "--" && <span className="text-rose-400/60 text-[10px] ml-1">(↓{downside}%)</span>}
              </p>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-gray-500 text-[11px] uppercase tracking-wider">Reward/Risk</p>
              <p className="text-white text-sm font-medium">{riskReward !== "--" ? `${riskReward}:1` : "--"}</p>
            </div>
          </div>
        </div>

        {/* AI Intelligence — tabbed */}
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col justify-between" onClick={(e) => e.stopPropagation()}>
          <div>
            <div className="flex items-center gap-1 mb-4">
              <button
                onClick={() => setTab("why")}
                className={`px-3 py-1 rounded-lg text-[10px] font-semibold uppercase tracking-wider transition border
                  ${tab === "why"
                    ? "bg-cyan-500/15 text-cyan-300 border-cyan-500/30"
                    : "text-gray-500 border-white/5 hover:text-gray-300"}`}
              >
                Why Trade
              </button>
              <button
                onClick={() => setTab("whynot")}
                className={`px-3 py-1 rounded-lg text-[10px] font-semibold uppercase tracking-wider transition border
                  ${tab === "whynot"
                    ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                    : "text-gray-500 border-white/5 hover:text-gray-300"}`}
              >
                Why NOT
              </button>
            </div>

            {tab === "why" && (
              <div className="space-y-2">
                {s.why?.slice(0, 3).map((r, i) => (
                  <p key={i} className="text-gray-300 text-xs leading-5">· {r}</p>
                ))}
                {(!s.why || s.why.length === 0) && (
                  <p className="text-gray-500 text-xs">No analysis available.</p>
                )}
              </div>
            )}

            {tab === "whynot" && (
              <div className="space-y-2">
                {whyNot.map((r, i) => (
                  <p key={i} className="text-rose-300/80 text-xs leading-5">⚠ {r}</p>
                ))}
              </div>
            )}
          </div>

          <Link
            to="/chat"
            onClick={(e) => e.stopPropagation()}
            className="mt-4 block text-center bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-300 py-2.5 rounded-xl transition text-xs font-semibold uppercase tracking-wider"
          >
            Discuss with AI Expert
          </Link>
        </div>
      </div>

      {/* Expand toggle */}
      <div className="border-t border-white/5 px-6 py-3 flex items-center justify-end">
        <p className="text-gray-600 text-xs">{expanded ? "▲ Collapse" : "▼ Full analysis"}</p>
      </div>

      {/* ── EXPANDED ── */}
      {expanded && (
        <div className="border-t border-white/5 px-6 py-5 space-y-5">
          <div className="bg-cyan-500/[0.04] border border-cyan-500/10 rounded-xl p-5">
            <p className="text-cyan-300 text-xs font-semibold uppercase tracking-wider mb-3">AI Trade Plan</p>
            <div className="space-y-2 text-sm">
              <p className="text-gray-300"><span className="text-gray-500">Best For: </span>{s.trade_plan?.best_for || "Swing Traders"}</p>
              <p className="text-gray-300"><span className="text-gray-500">Entry: </span>{s.trade_plan?.entry_strategy || "Wait near support and enter on bullish confirmation"}</p>
              <p className="text-gray-300"><span className="text-gray-500">SL: </span>{s.trade_plan?.stop_loss_strategy || "Strict stop loss below support zone"}</p>
              <p className="text-gray-300"><span className="text-gray-500">Target: </span>{s.trade_plan?.target_strategy || "Trail profits near resistance"}</p>
            </div>
          </div>

          <div>
            <p className="text-gray-500 text-xs uppercase tracking-wider mb-2">Multi Timeframe</p>
            <div className="grid grid-cols-3 gap-2">
              <InfoPill title="15m" value={s.multi_timeframe?.["15m"] || "Neutral"} />
              <InfoPill title="1h"  value={s.multi_timeframe?.["1h"]  || "Neutral"} />
              <InfoPill title="1D"  value={s.multi_timeframe?.["1d"]  || "Neutral"} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <InfoPill title="Institutional"  value={s.institutional_activity || "Neutral"} />
            <InfoPill title="News Sentiment" value={s.news_sentiment || "Mixed"} />
            <InfoPill title="Breakout Str."  value={s.breakout_strength != null ? `${s.breakout_strength}%` : "—"} />
            <InfoPill title="Signal Quality" value={s.signal_quality || "Moderate"} />
          </div>

          <div className="bg-white/[0.02] border border-white/5 rounded-xl px-4 py-3">
            <p className="text-sm text-gray-300 leading-6">{s.action || "No clear setup — wait for confirmation"}</p>
          </div>

          <Link
            to="/chat"
            onClick={(e) => e.stopPropagation()}
            className="block text-center bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 text-cyan-300 py-3 rounded-xl transition text-sm font-medium"
          >
            Ask AI Expert
          </Link>
        </div>
      )}
    </div>
  );
}

function InfoPill({ title, value }) {
  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-xl px-3 py-2">
      <p className="text-[10px] text-gray-500 mb-0.5">{title}</p>
      <p className="text-sm text-white font-medium">{value || "--"}</p>
    </div>
  );
}

export default Markets;
