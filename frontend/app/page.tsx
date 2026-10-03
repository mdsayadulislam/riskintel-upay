"use client";

import React, { useState, useEffect, useId } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Activity,
  Zap,
  Clock,
  Smartphone,
  Lock,
  MapPin,
  ArrowRightLeft,
  RefreshCw,
  Sparkles,
  Server,
  TrendingUp,
  Fingerprint,
  ChevronRight,
  Database,
  BarChart3,
  CheckCircle2,
  Info,
} from "lucide-react";

interface TxnFormData {
  txn_amount: number;
  hour_of_day: number;
  device_change_count_30d: number;
  velocity_last_1h: number;
  agent_distance_km: number;
  failed_pin_attempts_24h: number;
  is_cash_out: number;
}

interface KeyRiskDriver {
  feature: string;
  impact: number;
}

interface RiskAssessmentResult {
  risk_score: number;
  risk_level: string;
  recommended_action: string;
  key_risk_drivers: KeyRiskDriver[];
  narrative: string;
}

const DEFAULT_TXN: TxnFormData = {
  txn_amount: 500,
  hour_of_day: 14,
  device_change_count_30d: 0,
  velocity_last_1h: 1,
  agent_distance_km: 1.2,
  failed_pin_attempts_24h: 0,
  is_cash_out: 0,
};

const FEATURE_META: Record<string, { label: string; icon: any }> = {
  txn_amount: { label: "Transaction Amount", icon: Zap },
  hour_of_day: { label: "Transaction Hour", icon: Clock },
  device_change_count_30d: { label: "Device Changes (30d)", icon: Smartphone },
  velocity_last_1h: { label: "Velocity Spike (1h)", icon: Activity },
  agent_distance_km: { label: "Agent Distance", icon: MapPin },
  failed_pin_attempts_24h: { label: "Failed PIN Entries", icon: Lock },
  is_cash_out: { label: "Cash-Out Liquidation", icon: ArrowRightLeft },
};

export default function RiskIntelDashboard() {
  const [formData, setFormData] = useState<TxnFormData>(DEFAULT_TXN);
  const [result, setResult] = useState<RiskAssessmentResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [activeScenario, setActiveScenario] = useState<string>("scenario-1");
  const [lastAssessedAt, setLastAssessedAt] = useState<string>("");

  const amountInputId = useId();
  const hourInputId = useId();
  const deviceChangeInputId = useId();
  const velocityInputId = useId();
  const distanceInputId = useId();
  const pinAttemptsInputId = useId();
  const txnTypeSelectId = useId();

  // Check backend connectivity on mount
  useEffect(() => {
    checkBackendHealth();
    // Run initial assessment for default scenario
    evaluateTransaction(DEFAULT_TXN);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const res = await fetch("http://localhost:8000/health", {
        method: "GET",
        signal: AbortSignal.timeout(2000),
      });
      if (res.ok) {
        setBackendOnline(true);
      } else {
        setBackendOnline(false);
      }
    } catch {
      setBackendOnline(false);
    }
  };

  // Preset Scenario Handlers
  const loadScenario = (scenarioKey: string) => {
    setActiveScenario(scenarioKey);
    let scenarioData: TxnFormData;

    if (scenarioKey === "scenario-1") {
      // Scenario 1: Normal P2P
      scenarioData = {
        txn_amount: 500,
        hour_of_day: 14,
        velocity_last_1h: 1,
        failed_pin_attempts_24h: 0,
        device_change_count_30d: 0,
        agent_distance_km: 1.2,
        is_cash_out: 0,
      };
    } else if (scenarioKey === "scenario-2") {
      // Scenario 2: Account Takeover Attack
      scenarioData = {
        txn_amount: 25000,
        hour_of_day: 3,
        velocity_last_1h: 6,
        failed_pin_attempts_24h: 3,
        device_change_count_30d: 2,
        agent_distance_km: 18.5,
        is_cash_out: 1,
      };
    } else {
      // Scenario 3: Midnight Cash-out Anomaly
      scenarioData = {
        txn_amount: 18000,
        hour_of_day: 2,
        velocity_last_1h: 4,
        failed_pin_attempts_24h: 1,
        device_change_count_30d: 1,
        agent_distance_km: 8.0,
        is_cash_out: 1,
      };
    }

    setFormData(scenarioData);
    evaluateTransaction(scenarioData);
  };

  const handleInputChange = (field: keyof TxnFormData, value: number) => {
    setActiveScenario("custom");
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const evaluateTransaction = async (dataToAssess: TxnFormData) => {
    setLoading(true);
    const startTime = performance.now();

    try {
      const response = await fetch("http://localhost:8000/api/v1/assess-risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dataToAssess),
        signal: AbortSignal.timeout(4000),
      });

      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);

      if (response.ok) {
        const payload: RiskAssessmentResult = await response.json();
        setResult(payload);
        setBackendOnline(true);
        setLastAssessedAt(new Date().toLocaleTimeString());
      } else {
        throw new Error("Backend response error");
      }
    } catch {
      // Robust client-side fallback rule engine mirroring the LightGBM decision boundaries
      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);
      setBackendOnline(false);

      // Model calculation simulation
      let logit = -4.25;
      const isHighAmount = dataToAssess.txn_amount > 15000;
      const isMidnight = dataToAssess.hour_of_day >= 1 && dataToAssess.hour_of_day <= 4;
      const isMidnightSpike = isMidnight && dataToAssess.velocity_last_1h >= 3;
      const isMultiDevice = dataToAssess.device_change_count_30d >= 2;
      const isPinFail = dataToAssess.failed_pin_attempts_24h >= 2;

      if (isHighAmount) logit += 3.2;
      if (isMidnight) logit += 2.6;
      if (isMidnightSpike) logit += 2.5;
      if (isMultiDevice) logit += 2.75;
      if (isPinFail) logit += 3.1;
      if (dataToAssess.is_cash_out === 1) logit += 1.25;
      if (dataToAssess.velocity_last_1h >= 4) logit += 1.15;
      logit += 0.04 * Math.min(dataToAssess.agent_distance_km, 30);

      const prob = 1 / (1 + Math.exp(-logit));
      const score = Math.round(prob * 1000) / 10;

      // Extract SHAP proxy drivers
      const rawDrivers = [
        { feature: "txn_amount", impact: isHighAmount ? 3.099 : -0.75 },
        { feature: "failed_pin_attempts_24h", impact: isPinFail ? 2.753 : -0.39 },
        { feature: "device_change_count_30d", impact: isMultiDevice ? 2.149 : -0.34 },
        { feature: "hour_of_day", impact: isMidnight ? 2.451 : -0.25 },
        { feature: "velocity_last_1h", impact: dataToAssess.velocity_last_1h >= 4 ? 1.42 : -0.15 },
        { feature: "is_cash_out", impact: dataToAssess.is_cash_out === 1 ? 1.12 : -0.52 },
      ];
      const sortedDrivers = rawDrivers
        .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
        .slice(0, 3);
      const topDriversStr = sortedDrivers.map((d) => d.feature).join(", ");

      let action = "APPROVE";
      let level = "LOW";
      let narrative =
        "Transaction conforms to expected baseline behavior. Low fraud probability across velocity and biometric markers.";

      if (score >= 75) {
        action = "BLOCK_IMMEDIATELY";
        level = "HIGH";
        narrative = `Critical risk detected. Significant anomaly driven by ${topDriversStr}. Transaction halted; step-up audit mandated for upay operations.`;
      } else if (score >= 40) {
        action = "STEP_UP_2FA";
        level = "MEDIUM";
        narrative = `Moderate risk variance identified due to elevated ${topDriversStr}. Prompt user for biometric or SMS OTP challenge.`;
      }

      setResult({
        risk_score: score,
        risk_level: level,
        recommended_action: action,
        key_risk_drivers: sortedDrivers,
        narrative,
      });
      setLastAssessedAt(new Date().toLocaleTimeString());
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (action: string) => {
    switch (action) {
      case "BLOCK_IMMEDIATELY":
        return {
          bg: "bg-rose-500/10",
          border: "border-rose-500/40",
          text: "text-rose-400",
          badge: "bg-rose-600 text-white",
          glow: "shadow-[0_0_25px_rgba(239,68,68,0.25)]",
          dialColor: "#EF4444",
        };
      case "STEP_UP_2FA":
        return {
          bg: "bg-amber-500/10",
          border: "border-amber-500/40",
          text: "text-amber-400",
          badge: "bg-amber-500 text-black",
          glow: "shadow-[0_0_25px_rgba(245,158,11,0.25)]",
          dialColor: "#FFC107",
        };
      default:
        return {
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/40",
          text: "text-emerald-400",
          badge: "bg-emerald-600 text-white",
          glow: "shadow-[0_0_25px_rgba(16,185,129,0.25)]",
          dialColor: "#10B981",
        };
    }
  };

  const currentTheme = result ? getStatusColor(result.recommended_action) : getStatusColor("APPROVE");

  // SVG Gauge metrics
  const radius = 78;
  const circumference = 2 * Math.PI * radius;
  const scoreClamped = result ? Math.min(Math.max(result.risk_score, 0), 100) : 0;
  const strokeDashoffset = circumference - (scoreClamped / 100) * circumference;

  return (
    <div className="min-h-screen bg-[#0B132B] text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <header className="border-b border-[#1E2D56] bg-[#0E1738]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-[#FFB300] to-[#FFC107] flex items-center justify-center shadow-lg shadow-amber-500/20">
            <ShieldAlert className="h-6 w-6 text-[#0B132B] stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                RiskIntel <span className="text-[#FFC107]">upay</span>
              </h1>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-[#1E2D56] text-amber-300 border border-amber-500/30">
                Track 01: Trust & Risk Intelligence
              </span>
            </div>
            <p className="text-xs text-slate-400">
              UCB Fintech Real-Time AI Fraud Scoring & Local SHAP Explainability Engine
            </p>
          </div>
        </div>

        {/* System telemetry pill */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#111C3A] border border-[#1E2D56]">
            <Server className="h-3.5 w-3.5 text-slate-400" />
            <span className="text-slate-400">Backend:</span>
            {backendOnline === true ? (
              <span className="flex items-center gap-1.5 font-medium text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                FastAPI Live
              </span>
            ) : backendOnline === false ? (
              <span className="flex items-center gap-1.5 font-medium text-amber-400" title="Backend not detected on :8000; local model simulation fallback active">
                <span className="h-2 w-2 rounded-full bg-amber-400"></span>
                Local Simulation Fallback
              </span>
            ) : (
              <span className="flex items-center gap-1.5 font-medium text-slate-400">
                <RefreshCw className="h-3 w-3 animate-spin text-slate-400" />
                Connecting...
              </span>
            )}
          </div>

          {latencyMs !== null && (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#111C3A] border border-[#1E2D56] text-slate-300">
              <Activity className="h-3.5 w-3.5 text-[#FFC107]" />
              <span>Inference:</span>
              <span className="font-mono font-semibold text-white">{latencyMs} ms</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Grid Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

          {/* LEFT COLUMN: Real-Time Transaction Simulator */}
          <section className="lg:col-span-6 bg-[#111C3A] border border-[#1E2D56] rounded-2xl p-5 md:p-6 shadow-xl flex flex-col gap-6">
            <div className="flex items-center justify-between border-b border-[#1E2D56]/60 pb-4">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sliders className="h-5 w-5 text-[#FFC107]" />
                  Real-Time Transaction Simulator
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Configure synthetic or live MFS transaction vectors for risk inference
                </p>
              </div>
              <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-[#0B132B] text-slate-300 border border-[#1E2D56]">
                LightGBM + SHAP
              </span>
            </div>

            {/* Quick-Test Scenarios */}
            <div>
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-2.5 flex items-center justify-between">
                <span>Instant Quick-Test Scenarios</span>
                <span className="text-[10px] text-amber-400/80 lowercase">1-click presets</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                <button
                  type="button"
                  onClick={() => loadScenario("scenario-1")}
                  className={`text-left p-3 rounded-xl border transition-all flex flex-col justify-between ${
                    activeScenario === "scenario-1"
                      ? "bg-emerald-500/10 border-emerald-500/60 ring-1 ring-emerald-500/30 text-white"
                      : "bg-[#0E1738] border-[#1E2D56] hover:border-slate-600 text-slate-300 hover:bg-[#142048]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-400">Normal P2P</span>
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">500 BDT • 2 PM • 0 PIN fail</p>
                </button>

                <button
                  type="button"
                  onClick={() => loadScenario("scenario-2")}
                  className={`text-left p-3 rounded-xl border transition-all flex flex-col justify-between ${
                    activeScenario === "scenario-2"
                      ? "bg-rose-500/15 border-rose-500/60 ring-1 ring-rose-500/30 text-white"
                      : "bg-[#0E1738] border-[#1E2D56] hover:border-slate-600 text-slate-300 hover:bg-[#142048]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-rose-400">ATO Attack</span>
                    <AlertTriangle className="h-4 w-4 text-rose-400" />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">25k BDT • 3 AM • 3 PIN fail</p>
                </button>

                <button
                  type="button"
                  onClick={() => loadScenario("scenario-3")}
                  className={`text-left p-3 rounded-xl border transition-all flex flex-col justify-between ${
                    activeScenario === "scenario-3"
                      ? "bg-amber-500/15 border-amber-500/60 ring-1 ring-amber-500/30 text-white"
                      : "bg-[#0E1738] border-[#1E2D56] hover:border-slate-600 text-slate-300 hover:bg-[#142048]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-400">Midnight Cashout</span>
                    <Fingerprint className="h-4 w-4 text-amber-400" />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">18k BDT • 2 AM • 4 Vel</p>
                </button>
              </div>
            </div>

            {/* Feature Form Inputs */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                evaluateTransaction(formData);
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* 1. Transaction Amount */}
                <div className="space-y-1.5">
                  <label htmlFor={amountInputId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Zap className="h-3.5 w-3.5 text-[#FFC107]" />
                      Amount (BDT)
                    </span>
                    <span className="text-[11px] font-mono text-amber-400">
                      ৳{formData.txn_amount.toLocaleString()}
                    </span>
                  </label>
                  <input
                    id={amountInputId}
                    type="number"
                    min="10"
                    max="100000"
                    step="50"
                    value={formData.txn_amount}
                    onChange={(e) => handleInputChange("txn_amount", parseFloat(e.target.value) || 0)}
                    className="w-full bg-[#0E1738] border border-[#1E2D56] focus:border-[#FFC107] focus:ring-1 focus:ring-[#FFC107] rounded-xl px-3 py-2 text-sm text-white font-mono outline-none transition"
                    required
                  />
                  <span className="text-[10px] text-slate-400">upay daily limit ceiling ~৳25,000</span>
                </div>

                {/* 2. Hour of Day */}
                <div className="space-y-1.5">
                  <label htmlFor={hourInputId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-[#FFC107]" />
                      Hour of Day (0-23)
                    </span>
                    <span className="text-[11px] font-mono text-slate-300">
                      {formData.hour_of_day.toString().padStart(2, "0")}:00 hrs
                    </span>
                  </label>
                  <input
                    id={hourInputId}
                    type="number"
                    min="0"
                    max="23"
                    value={formData.hour_of_day}
                    onChange={(e) => handleInputChange("hour_of_day", parseInt(e.target.value) || 0)}
                    className="w-full bg-[#0E1738] border border-[#1E2D56] focus:border-[#FFC107] focus:ring-1 focus:ring-[#FFC107] rounded-xl px-3 py-2 text-sm text-white font-mono outline-none transition"
                    required
                  />
                  <span className="text-[10px] text-slate-400">Hours 1-4 represent midnight high-risk lull</span>
                </div>

                {/* 3. Device Changes in 30d */}
                <div className="space-y-1.5">
                  <label htmlFor={deviceChangeInputId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Smartphone className="h-3.5 w-3.5 text-[#FFC107]" />
                      Device Changes (30d)
                    </span>
                    <span className="text-[11px] font-mono text-slate-300">{formData.device_change_count_30d}</span>
                  </label>
                  <input
                    id={deviceChangeInputId}
                    type="number"
                    min="0"
                    max="10"
                    value={formData.device_change_count_30d}
                    onChange={(e) => handleInputChange("device_change_count_30d", parseInt(e.target.value) || 0)}
                    className="w-full bg-[#0E1738] border border-[#1E2D56] focus:border-[#FFC107] focus:ring-1 focus:ring-[#FFC107] rounded-xl px-3 py-2 text-sm text-white font-mono outline-none transition"
                    required
                  />
                  <span className="text-[10px] text-slate-400">&ge; 2 flags possible SIM swap / ATO</span>
                </div>

                {/* 4. Velocity Last 1h */}
                <div className="space-y-1.5">
                  <label htmlFor={velocityInputId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5 text-[#FFC107]" />
                      Velocity (Last 1h)
                    </span>
                    <span className="text-[11px] font-mono text-slate-300">{formData.velocity_last_1h} txns</span>
                  </label>
                  <input
                    id={velocityInputId}
                    type="number"
                    min="0"
                    max="20"
                    value={formData.velocity_last_1h}
                    onChange={(e) => handleInputChange("velocity_last_1h", parseInt(e.target.value) || 0)}
                    className="w-full bg-[#0E1738] border border-[#1E2D56] focus:border-[#FFC107] focus:ring-1 focus:ring-[#FFC107] rounded-xl px-3 py-2 text-sm text-white font-mono outline-none transition"
                    required
                  />
                  <span className="text-[10px] text-slate-400">Burst drain attempts trigger alerts</span>
                </div>

                {/* 5. Agent Distance in KM */}
                <div className="space-y-1.5">
                  <label htmlFor={distanceInputId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-[#FFC107]" />
                      Agent Distance (km)
                    </span>
                    <span className="text-[11px] font-mono text-slate-300">{formData.agent_distance_km} km</span>
                  </label>
                  <input
                    id={distanceInputId}
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    value={formData.agent_distance_km}
                    onChange={(e) => handleInputChange("agent_distance_km", parseFloat(e.target.value) || 0)}
                    className="w-full bg-[#0E1738] border border-[#1E2D56] focus:border-[#FFC107] focus:ring-1 focus:ring-[#FFC107] rounded-xl px-3 py-2 text-sm text-white font-mono outline-none transition"
                    required
                  />
                  <span className="text-[10px] text-slate-400">Geospatial proximity to cash-out point</span>
                </div>

                {/* 6. Failed PIN Attempts (24h) */}
                <div className="space-y-1.5">
                  <label htmlFor={pinAttemptsInputId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Lock className="h-3.5 w-3.5 text-[#FFC107]" />
                      Failed PIN Attempts (24h)
                    </span>
                    <span className="text-[11px] font-mono text-slate-300">{formData.failed_pin_attempts_24h}</span>
                  </label>
                  <input
                    id={pinAttemptsInputId}
                    type="number"
                    min="0"
                    max="10"
                    value={formData.failed_pin_attempts_24h}
                    onChange={(e) => handleInputChange("failed_pin_attempts_24h", parseInt(e.target.value) || 0)}
                    className="w-full bg-[#0E1738] border border-[#1E2D56] focus:border-[#FFC107] focus:ring-1 focus:ring-[#FFC107] rounded-xl px-3 py-2 text-sm text-white font-mono outline-none transition"
                    required
                  />
                  <span className="text-[10px] text-slate-400">&ge; 2 indicates credential guessing</span>
                </div>
              </div>

              {/* 7. Transaction Type (Cash Out vs P2P Send Money) */}
              <div className="space-y-1.5 pt-2">
                <label htmlFor={txnTypeSelectId} className="text-xs font-medium text-slate-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <ArrowRightLeft className="h-3.5 w-3.5 text-[#FFC107]" />
                    Transaction Channel / Type
                  </span>
                  <span className="text-[11px] font-semibold text-amber-300">
                    {formData.is_cash_out === 1 ? "Agent Cash-Out" : "P2P Send Money"}
                  </span>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    id={txnTypeSelectId}
                    type="button"
                    onClick={() => handleInputChange("is_cash_out", 0)}
                    className={`py-2.5 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition ${
                      formData.is_cash_out === 0
                        ? "bg-[#1E2D56] border-[#FFC107] text-[#FFC107] ring-1 ring-[#FFC107]/40"
                        : "bg-[#0E1738] border-[#1E2D56] text-slate-400 hover:text-white"
                    }`}
                  >
                    <span>P2P Send Money (0)</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleInputChange("is_cash_out", 1)}
                    className={`py-2.5 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition ${
                      formData.is_cash_out === 1
                        ? "bg-[#1E2D56] border-[#FFC107] text-[#FFC107] ring-1 ring-[#FFC107]/40"
                        : "bg-[#0E1738] border-[#1E2D56] text-slate-400 hover:text-white"
                    }`}
                  >
                    <span>Agent Cash-Out (1)</span>
                  </button>
                </div>
              </div>

              {/* Submit CTA */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-[#FFC107] via-[#FFB300] to-[#FFA000] text-[#0B132B] font-bold text-sm tracking-wide shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:brightness-105 active:scale-[0.99] transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin text-[#0B132B]" />
                      <span>Computing LightGBM Risk & SHAP Trees...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 text-[#0B132B]" />
                      <span>Run Real-Time Risk Assessment</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </section>

          {/* RIGHT COLUMN: Live Analyst Triage Verdict */}
          <section className="lg:col-span-6 space-y-6">
            {/* Main Verdict Card */}
            <div className={`rounded-2xl border ${currentTheme.border} ${currentTheme.bg} ${currentTheme.glow} p-6 backdrop-blur-sm transition-all duration-300 relative overflow-hidden`}>
              
              {/* Card Header */}
              <div className="flex items-center justify-between border-b border-slate-700/40 pb-4">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-[#0B132B]/80 border border-slate-700/50">
                    <BarChart3 className="h-5 w-5 text-[#FFC107]" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white tracking-wide">
                      Live Analyst Triage Verdict
                    </h2>
                    <p className="text-xs text-slate-400">
                      Track 01 Governance Policy & Decision Engine
                    </p>
                  </div>
                </div>

                {lastAssessedAt && (
                  <span className="text-[11px] font-mono text-slate-400 bg-[#0B132B]/60 px-2.5 py-1 rounded-md border border-slate-700/40">
                    {lastAssessedAt}
                  </span>
                )}
              </div>

              {/* Gauge & Verdict Badge Section */}
              <div className="py-6 flex flex-col sm:flex-row items-center justify-around gap-6">
                
                {/* Animated Circular Gauge */}
                <div className="relative flex items-center justify-center">
                  <svg className="w-48 h-48 transform -rotate-90">
                    {/* Background track */}
                    <circle
                      cx="96"
                      cy="96"
                      r={radius}
                      stroke="#1E2D56"
                      strokeWidth="13"
                      fill="transparent"
                      className="opacity-60"
                    />
                    {/* Animated Progress Arc */}
                    <circle
                      cx="96"
                      cy="96"
                      r={radius}
                      stroke={currentTheme.dialColor}
                      strokeWidth="13"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      fill="transparent"
                      className="transition-all duration-700 ease-out"
                    />
                  </svg>

                  {/* Centered Score Readout */}
                  <div className="absolute flex flex-col items-center justify-center text-center">
                    <span className="text-[11px] uppercase font-bold tracking-widest text-slate-400">
                      Risk Score
                    </span>
                    <span className="text-4xl font-black font-mono tracking-tight text-white mt-0.5">
                      {result ? result.risk_score.toFixed(1) : "--"}
                    </span>
                    <span className="text-[11px] font-medium text-slate-400">
                      out of 100
                    </span>
                  </div>
                </div>

                {/* Verdict Summary Pillar */}
                <div className="flex flex-col items-center sm:items-start text-center sm:text-left gap-2.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Recommended Policy Action
                  </span>

                  <div className={`px-4 py-2 rounded-xl font-mono font-bold text-sm tracking-wide uppercase shadow-lg ${currentTheme.badge}`}>
                    {result ? result.recommended_action : "AWAITING_INPUT"}
                  </div>

                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-400">Risk Tier:</span>
                    <span className={`text-xs font-bold uppercase tracking-wider ${currentTheme.text}`}>
                      {result ? `${result.risk_level} RISK` : "--"}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-400 max-w-[210px]">
                    {result?.recommended_action === "BLOCK_IMMEDIATELY"
                      ? "High-confidence fraud signal. Upay account halted pending step-up verification."
                      : result?.recommended_action === "STEP_UP_2FA"
                      ? "Secondary factor challenge required before dispatching funds."
                      : "Standard legitimate transaction baseline. Fast-track approval."}
                  </p>
                </div>
              </div>

              {/* Analyst Investigation Narrative Card */}
              <div className="mt-2 bg-[#0B132B]/80 border border-slate-700/60 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2 text-xs font-bold uppercase tracking-wider text-amber-300">
                  <Info className="h-4 w-4" />
                  <span>Analyst Investigation Narrative</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">
                  {result
                    ? result.narrative
                    : "Awaiting real-time transaction feature input to synthesize local analyst briefing."}
                </p>
              </div>

              {/* SHAP Risk Factor Attribution Card */}
              <div className="mt-4 bg-[#0B132B]/80 border border-slate-700/60 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3 text-xs">
                  <span className="font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <TrendingUp className="h-4 w-4 text-[#FFC107]" />
                    SHAP Risk Factor Attribution (Top 3 Drivers)
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Local Explainability</span>
                </div>

                {result && result.key_risk_drivers && result.key_risk_drivers.length > 0 ? (
                  <div className="space-y-3">
                    {result.key_risk_drivers.map((driver, index) => {
                      const isRiskElevating = driver.impact > 0;
                      const absImpact = Math.abs(driver.impact);
                      // Normalize bar width to max 100% based on impact scale ~ 6.0
                      const barWidth = Math.min(Math.max((absImpact / 5.0) * 100, 15), 100);
                      const meta = FEATURE_META[driver.feature] || {
                        label: driver.feature,
                        icon: Zap,
                      };
                      const IconComponent = meta.icon;

                      return (
                        <div key={index} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-medium text-slate-300 flex items-center gap-1.5">
                              <IconComponent className="h-3.5 w-3.5 text-slate-400" />
                              {meta.label}
                            </span>
                            <span
                              className={`font-mono text-[11px] font-semibold ${
                                isRiskElevating ? "text-rose-400" : "text-emerald-400"
                              }`}
                            >
                              {driver.impact > 0 ? `+${driver.impact.toFixed(4)}` : driver.impact.toFixed(4)}
                              <span className="text-[10px] text-slate-400 ml-1">
                                {isRiskElevating ? "(elevates risk)" : "(mitigates risk)"}
                              </span>
                            </span>
                          </div>

                          {/* Horizontal Attribution Bar */}
                          <div className="w-full bg-[#111C3A] rounded-full h-2 overflow-hidden border border-slate-700/40">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isRiskElevating
                                  ? "bg-gradient-to-r from-amber-500 to-rose-500"
                                  : "bg-gradient-to-r from-emerald-500 to-teal-400"
                              }`}
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No attribution drivers loaded yet.</p>
                )}
              </div>

              {/* Bottom Operational Checklist */}
              <div className="mt-4 pt-3 border-t border-slate-700/40 grid grid-cols-3 gap-2 text-center">
                <div className="bg-[#111C3A]/60 rounded-lg p-2 border border-slate-700/40">
                  <span className="block text-[10px] text-slate-400 uppercase">Engine Status</span>
                  <span className="text-xs font-semibold text-emerald-400 flex items-center justify-center gap-1 mt-0.5">
                    <CheckCircle2 className="h-3 w-3" /> Ready
                  </span>
                </div>
                <div className="bg-[#111C3A]/60 rounded-lg p-2 border border-slate-700/40">
                  <span className="block text-[10px] text-slate-400 uppercase">Model Tree</span>
                  <span className="text-xs font-mono font-semibold text-white mt-0.5">
                    LGBM (100 Est)
                  </span>
                </div>
                <div className="bg-[#111C3A]/60 rounded-lg p-2 border border-slate-700/40">
                  <span className="block text-[10px] text-slate-400 uppercase">Compliance</span>
                  <span className="text-xs font-semibold text-amber-300 mt-0.5">
                    Audit Trail Active
                  </span>
                </div>
              </div>

            </div>
          </section>

        </div>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-[#1E2D56] bg-[#0E1738]/60 px-6 py-4 text-center text-xs text-slate-400">
        <p>
          RiskIntel upay &copy; {new Date().getFullYear()} UCB Fintech Ltd. &bull; Track 01: Trust &amp; Risk Intelligence &bull; Built with FastAPI, LightGBM, SHAP &amp; Next.js 14
        </p>
      </footer>
    </div>
  );
}

function Sliders(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="4" x2="4" y1="21" y2="14" />
      <line x1="4" x2="4" y1="10" y2="3" />
      <line x1="12" x2="12" y1="21" y2="12" />
      <line x1="12" x2="12" y1="8" y2="3" />
      <line x1="20" x2="20" y1="21" y2="16" />
      <line x1="20" x2="20" y1="12" y2="3" />
      <line x1="2" x2="6" y1="14" y2="14" />
      <line x1="10" x2="14" y1="8" y2="8" />
      <line x1="18" x2="22" y1="16" y2="16" />
    </svg>
  );
}
