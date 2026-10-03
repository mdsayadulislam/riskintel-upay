'use client';

import React, { useState, useEffect, useRef } from 'react';
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
  CheckCircle2,
  Info,
  QrCode,
  Home,
  User,
  History,
  Menu,
  Eye,
  EyeOff,
  Bell,
  Sliders,
  Wifi,
  Battery,
  Signal,
  Send,
  Building2,
  RotateCcw,
  X,
  PhoneCall,
  KeyRound,
  Check,
  PlusCircle,
} from 'lucide-react';

// ============================================================================
// 1. TYPES & DATA CONTRACTS
// ============================================================================
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
  inference_time_ms?: number;
}

// ============================================================================
// 2. REGULATORY CONSTANTS & PERSISTENCE KEYS
// ============================================================================
const LS_BALANCE_KEY = 'riskintel_upay_balance';
const LS_FORM_KEY = 'riskintel_upay_form';
const LS_RESULT_KEY = 'riskintel_upay_result';
const LS_SCENARIO_KEY = 'riskintel_upay_scenario';
const LS_ASSESSED_KEY = 'riskintel_upay_last_assessed';

const ACCOUNT_INITIAL_BALANCE = 35000.0;
const DEFAULT_AMOUNT = 500;
const MAX_DAILY_LIMIT = 25000;

const DEFAULT_TXN: TxnFormData = {
  txn_amount: DEFAULT_AMOUNT,
  hour_of_day: 14,
  device_change_count_30d: 0,
  velocity_last_1h: 1,
  agent_distance_km: 1.2,
  failed_pin_attempts_24h: 0,
  is_cash_out: 0,
};

const INITIAL_RESULT: RiskAssessmentResult = {
  risk_score: 0.05,
  risk_level: 'LOW',
  recommended_action: 'APPROVE',
  key_risk_drivers: [
    { feature: 'txn_amount', impact: -0.6139 },
    { feature: 'is_cash_out', impact: -0.3993 },
    { feature: 'device_change_count_30d', impact: -0.3434 },
  ],
  narrative:
    'Transaction conforms to expected baseline behavior. Low anomaly probability across biometric and velocity signals.',
  inference_time_ms: 8.5,
};

const FEATURE_META: Record<string, { label: string; bnLabel: string; icon: any }> = {
  txn_amount: { label: 'Transaction Amount', bnLabel: 'লেনদেনের পরিমাণ', icon: Zap },
  hour_of_day: { label: 'Transaction Hour', bnLabel: 'লেনদেনের সময়', icon: Clock },
  device_change_count_30d: { label: 'Device Changes (30d)', bnLabel: 'ডিভাইস পরিবর্তন', icon: Smartphone },
  velocity_last_1h: { label: 'Velocity (1h)', bnLabel: '১ ঘণ্টার ফ্রিকোয়েন্সি', icon: Activity },
  agent_distance_km: { label: 'Agent Distance', bnLabel: 'এজেন্টের দূরত্ব (কিমি)', icon: MapPin },
  failed_pin_attempts_24h: { label: 'Failed PIN Attempts', bnLabel: 'ভুল পিন চেষ্টা (২৪ ঘণ্টা)', icon: Lock },
  is_cash_out: { label: 'Cash-Out Operation', bnLabel: 'ক্যাশ-আউট অপারেশন', icon: ArrowRightLeft },
};

// ============================================================================
// 3. SUBCOMPONENTS
// ============================================================================

/** In-App Modal Overlay for upay Mobile App */
interface ModalProps {
  isOpen: boolean;
  result: RiskAssessmentResult;
  formData: TxnFormData;
  balance: number;
  onClose: () => void;
  on2FAVerify: () => void;
  onSelfServiceRecovery: () => void;
  verifyingOtp: boolean;
  otpVerified: boolean;
  recoveryMode: boolean;
  recovering: boolean;
  recoverySuccess: boolean;
  setRecoveryMode: (val: boolean) => void;
}

function TransactionFeedbackModal({
  isOpen,
  result,
  formData,
  balance,
  onClose,
  on2FAVerify,
  onSelfServiceRecovery,
  verifyingOtp,
  otpVerified,
  recoveryMode,
  recovering,
  recoverySuccess,
  setRecoveryMode,
}: ModalProps) {
  if (!isOpen) return null;

  const currentAmount = Number(formData.txn_amount) || 0;

  return (
    <div className="absolute inset-0 z-30 bg-[#063254]/60 backdrop-blur-sm flex items-end justify-center p-3 animate-in fade-in duration-200">
      <div className="w-full bg-white rounded-3xl p-5 shadow-2xl border border-slate-200 space-y-4 animate-in slide-in-from-bottom-5 duration-300">
        
        {/* Header with Title and Dismiss Button */}
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="h-6 w-1.5 bg-[#FFC800] rounded-full"></div>
            <span className="text-xs font-bold text-[#063254] uppercase tracking-wider">
              upay লেনদেন পর্যবেক্ষণ
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="h-7 w-7 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* 1. APPROVE Modal */}
        {result.recommended_action === 'APPROVE' && (
          <div className="text-center space-y-3 py-1">
            <div className="h-16 w-16 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shadow-inner">
              <CheckCircle2 className="h-10 w-10 stroke-[2.2]" />
            </div>
            <div>
              <h3 className="text-lg font-black text-emerald-700">
                লেনদেন সফল হয়েছে!
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                আপনার ফান্ড ট্রান্সফার সফলভাবে সম্পন্ন হয়েছে।
              </p>
            </div>

            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 space-y-2 text-left text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-500">প্রেরিত পরিমাণ:</span>
                <span className="font-mono font-bold text-[#063254] text-sm">
                  ৳ {currentAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">প্রাপক:</span>
                <span className="font-bold text-[#063254]">
                  {formData.is_cash_out === 1 ? 'upay এজেন্ট (#88219)' : '01812-345678 (User)'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">নতুন অবশিষ্ট ব্যালেন্স:</span>
                <span className="font-mono font-bold text-emerald-600">
                  ৳ {balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="flex justify-between items-center pt-1 border-t border-slate-200/80">
                <span className="text-slate-400 text-[10px]">ট্রানজেকশন আইডি:</span>
                <span className="font-mono text-[10px] font-bold text-slate-600">UP9472A802</span>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="w-full py-3 rounded-2xl bg-[#063254] hover:bg-[#08416C] text-white font-bold text-xs tracking-wide shadow-md active:scale-95 transition cursor-pointer"
            >
              হোমে ফিরে যান
            </button>
          </div>
        )}

        {/* 2. STEP_UP_2FA Modal */}
        {result.recommended_action === 'STEP_UP_2FA' && (
          <div className="text-center space-y-3 py-1">
            <div className="h-16 w-16 mx-auto rounded-full bg-amber-100 text-amber-600 flex items-center justify-center shadow-inner">
              <KeyRound className="h-9 w-9 stroke-[2.2]" />
            </div>
            <div>
              <h3 className="text-base font-black text-amber-800">
                অতিরিক্ত সুরক্ষা যাচাই (2FA) আবশ্যক!
              </h3>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                নিরাপত্তাজনিত কারণে আপনার ডিভাইসে ৬-সংখ্যার ওটিপি কোড পাঠানো হয়েছে।
              </p>
            </div>

            <div className="py-2">
              <div className="flex items-center justify-center gap-2">
                {['8', '4', '1', '9', '2', '0'].map((digit, idx) => (
                  <div
                    key={idx}
                    className="h-10 w-9 rounded-xl border-2 border-[#063254] bg-white flex items-center justify-center font-mono font-black text-base text-[#063254] shadow-sm"
                  >
                    {digit}
                  </div>
                ))}
              </div>
              <span className="text-[10px] text-slate-400 mt-2 block">
                কোডের মেয়াদ শেষ হবে: <span className="font-bold text-[#063254]">০:৪৫ সেকেন্ড</span>
              </span>
            </div>

            {otpVerified ? (
              <div className="space-y-3">
                <div className="p-3 bg-emerald-50 rounded-2xl border border-emerald-300 text-emerald-700 text-xs font-bold flex items-center justify-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span>২-স্তর ওটিপি সফলভাবে যাচাই হয়েছে! ফান্ড ট্রান্সফার সম্পন্ন।</span>
                </div>
                <div className="flex justify-between items-center text-xs px-2 text-slate-600">
                  <span>নতুন অবশিষ্ট ব্যালেন্স:</span>
                  <span className="font-bold font-mono text-emerald-600">
                    ৳ {balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full py-2.5 rounded-2xl bg-[#063254] text-white font-bold text-xs"
                >
                  হোমে ফিরে যান
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={on2FAVerify}
                disabled={verifyingOtp}
                className="w-full py-3 rounded-2xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs tracking-wide shadow-md active:scale-95 transition cursor-pointer flex items-center justify-center gap-2"
              >
                {verifyingOtp ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>যাচাই হচ্ছে...</span>
                  </>
                ) : (
                  <span>যাচাই করুন ও সম্পন্ন করুন</span>
                )}
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              className="text-xs font-bold text-slate-500 hover:text-slate-700 cursor-pointer pt-1"
            >
              বাতিল করুন
            </button>
          </div>
        )}

        {/* 3. BLOCK_IMMEDIATELY Modal with Self-Service Recovery */}
        {result.recommended_action === 'BLOCK_IMMEDIATELY' && (
          <div className="text-center space-y-3 py-1">
            {!recoveryMode && (
              <>
                <div className="h-16 w-16 mx-auto rounded-full bg-red-100 text-red-600 flex items-center justify-center shadow-inner">
                  <ShieldAlert className="h-10 w-10 stroke-[2.2]" />
                </div>
                <div>
                  <h3 className="text-base font-black text-red-700">
                    লেনদেনটি স্থগিত করা হয়েছে!
                  </h3>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    অস্বাভাবিক কার্যকলাপ বা ঝুঁকির কারণে লেনদেনটি সিস্টেম দ্বারা বাতিল করা হয়েছে। প্রয়োজনে কল করুন upay হেল্পলাইন ১৬২৬৮।
                  </p>
                </div>

                <div className="bg-red-50 p-3 rounded-2xl border border-red-200 text-left space-y-1">
                  <span className="text-[10px] font-bold text-red-800 uppercase block">
                    স্থগিতাদেশের কারণ:
                  </span>
                  <span className="text-xs font-semibold text-red-700 block">
                    অ্যাকাউন্ট টেকওভার / মধ্যরাত অস্বাভাবিক লেনদেন প্যাটার্ন
                  </span>
                </div>

                <div className="space-y-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setRecoveryMode(true)}
                    className="w-full py-3 px-4 rounded-2xl bg-[#063254] hover:bg-[#08416C] text-[#FFC800] font-bold text-xs tracking-wide shadow-md flex items-center justify-center gap-2 active:scale-95 transition cursor-pointer"
                  >
                    <KeyRound className="h-4 w-4 text-[#FFC800]" />
                    <span>ওটিপি ও বায়োমেট্রিক দিয়ে তাৎক্ষণিক আনলক করুন</span>
                  </button>

                  <div className="grid grid-cols-2 gap-2">
                    <a
                      href="tel:16268"
                      className="py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-[#063254] font-bold text-xs flex items-center justify-center gap-1.5 transition block text-center"
                    >
                      <PhoneCall className="h-3.5 w-3.5" />
                      <span>কল ১৬২৬৮</span>
                    </a>
                    <button
                      type="button"
                      onClick={onClose}
                      className="py-2.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold text-xs transition cursor-pointer"
                    >
                      অবহিত হলাম
                    </button>
                  </div>
                </div>
              </>
            )}

            {recoveryMode && !recoverySuccess && (
              <div className="space-y-3 animate-in fade-in">
                <div className="h-14 w-14 mx-auto rounded-full bg-amber-100 text-amber-700 flex items-center justify-center shadow-inner">
                  <Fingerprint className="h-8 w-8 stroke-[2.2]" />
                </div>
                <div>
                  <h3 className="text-sm font-black text-[#063254]">
                    জরুরি আইডেন্টিটি রিকভারি (Self-Service Unlock)
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-1">
                    আপনার নিবন্ধিত ডিভাইসে প্রেরিত ৬-সংখ্যার জরুরি ওটিপি কোড (১২৩৪৫৬) প্রদান করুন:
                  </p>
                </div>

                <div className="flex items-center justify-center gap-2 py-1">
                  {['1', '2', '3', '4', '5', '6'].map((digit, idx) => (
                    <div
                      key={idx}
                      className="h-10 w-9 rounded-xl border-2 border-[#063254] bg-white flex items-center justify-center font-mono font-black text-base text-[#063254] shadow-sm"
                    >
                      {digit}
                    </div>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={onSelfServiceRecovery}
                  disabled={recovering}
                  className="w-full py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs tracking-wide shadow-md active:scale-95 transition cursor-pointer flex items-center justify-center gap-2"
                >
                  {recovering ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span>আইডেন্টিটি যাচাই হচ্ছে...</span>
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4" />
                      <span>যাচাই করুন ও আনলক করুন</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => setRecoveryMode(false)}
                  className="text-xs font-bold text-slate-400 hover:text-slate-600"
                >
                  পিছনে যান
                </button>
              </div>
            )}

            {recoveryMode && recoverySuccess && (
              <div className="space-y-3 py-1 animate-in zoom-in-95">
                <div className="h-16 w-16 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center shadow-inner">
                  <CheckCircle2 className="h-10 w-10 stroke-[2.2]" />
                </div>
                <div>
                  <h3 className="text-base font-black text-emerald-700">
                    আইডেন্টিটি যাচাই সম্পন্ন!
                  </h3>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    জরুরি লেনদেন সফল হয়েছে এবং সুরক্ষা নিষেধাজ্ঞা প্রত্যাহার করা হয়েছে।
                  </p>
                </div>

                <div className="bg-emerald-50 p-3.5 rounded-2xl border border-emerald-200 text-xs text-left space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">সম্পন্ন লেনদেন:</span>
                    <span className="font-bold font-mono text-[#063254]">
                      ৳ {currentAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">নতুন ব্যালেন্স:</span>
                    <span className="font-bold font-mono text-emerald-700">
                      ৳ {balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-[10px] text-slate-500 pt-1 border-t border-emerald-200/60">
                    <span>পিন ব্যর্থতা রিসেট:</span>
                    <span className="font-bold text-emerald-700">০ (স্বাভাবিক)</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={onClose}
                  className="w-full py-3 rounded-2xl bg-[#063254] text-white font-bold text-xs tracking-wide shadow-md active:scale-95 transition cursor-pointer"
                >
                  হোমে ফিরে যান
                </button>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

// ============================================================================
// 4. MAIN ORCHESTRATOR COMPONENT
// ============================================================================
export default function RiskIntelUpayDashboard() {
  const [formData, setFormData] = useState<TxnFormData>(DEFAULT_TXN);
  const [balance, setBalance] = useState<number>(ACCOUNT_INITIAL_BALANCE);
  const [result, setResult] = useState<RiskAssessmentResult>(INITIAL_RESULT);
  const [loading, setLoading] = useState<boolean>(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [activeScenario, setActiveScenario] = useState<string>('scenario-1');
  const [lastAssessedAt, setLastAssessedAt] = useState<string>('');
  const [showBalance, setShowBalance] = useState<boolean>(false);
  const [referenceNote, setReferenceNote] = useState<string>('');
  const [pin, setPin] = useState<string>('1234');
  const [isHydrated, setIsHydrated] = useState<boolean>(false);

  // Modal State
  const [showModal, setShowModal] = useState<boolean>(false);
  const [otpVerified, setOtpVerified] = useState<boolean>(false);
  const [verifyingOtp, setVerifyingOtp] = useState<boolean>(false);
  const [recoveryMode, setRecoveryMode] = useState<boolean>(false);
  const [recovering, setRecovering] = useState<boolean>(false);
  const [recoverySuccess, setRecoverySuccess] = useState<boolean>(false);

  // Dynamic API configuration with fallback for production deployments
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
  const API_ASSESS_URL = `${API_BASE}/api/v1/assess-risk`;
  const API_HEALTH_URL = `${API_BASE}/health`;
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Hydrate State from LocalStorage on mount
  useEffect(() => {
    try {
      const savedBalance = localStorage.getItem(LS_BALANCE_KEY);
      if (savedBalance) {
        const parsedBalance = parseFloat(savedBalance);
        if (!isNaN(parsedBalance)) setBalance(parsedBalance);
      }

      const savedForm = localStorage.getItem(LS_FORM_KEY);
      if (savedForm) {
        const parsedForm = JSON.parse(savedForm);
        if (parsedForm && typeof parsedForm.txn_amount === 'number') {
          setFormData(parsedForm);
        }
      }

      const savedResult = localStorage.getItem(LS_RESULT_KEY);
      if (savedResult) {
        const parsedResult = JSON.parse(savedResult);
        if (parsedResult && typeof parsedResult.risk_score === 'number') {
          setResult(parsedResult);
        }
      }

      const savedScenario = localStorage.getItem(LS_SCENARIO_KEY);
      if (savedScenario) setActiveScenario(savedScenario);

      const savedAssessed = localStorage.getItem(LS_ASSESSED_KEY);
      if (savedAssessed) setLastAssessedAt(savedAssessed);
    } catch (e) {
      console.error('LocalStorage hydration failed:', e);
    } finally {
      setIsHydrated(true);
    }

    checkBackendHealth();
  }, []);

  // Persist State to LocalStorage
  useEffect(() => {
    if (!isHydrated) return;
    try {
      localStorage.setItem(LS_BALANCE_KEY, balance.toString());
      localStorage.setItem(LS_FORM_KEY, JSON.stringify(formData));
      localStorage.setItem(LS_RESULT_KEY, JSON.stringify(result));
      localStorage.setItem(LS_SCENARIO_KEY, activeScenario);
      if (lastAssessedAt) localStorage.setItem(LS_ASSESSED_KEY, lastAssessedAt);
    } catch (e) {
      console.error('LocalStorage persistence error:', e);
    }
  }, [formData, balance, result, activeScenario, lastAssessedAt, isHydrated]);

  const checkBackendHealth = async () => {
    try {
      const res = await fetch(API_HEALTH_URL, {
        method: 'GET',
        signal: AbortSignal.timeout(2500),
      });
      setBackendOnline(res.ok);
    } catch {
      setBackendOnline(false);
    }
  };

  // MFS Validation Logic
  const minAmount = formData.is_cash_out === 1 ? 50 : 10;
  const currentAmount = Number(formData.txn_amount) || 0;

  const getValidationError = (amt: number, isCashOut: number, curBalance: number): string | null => {
    if (isNaN(amt) || amt <= 0) return 'অনুগ্রহ করে বৈধ লেনদেন পরিমাণ লিখুন';
    if (amt > MAX_DAILY_LIMIT) return 'দৈনিক লেনদেন সীমা অতিক্রম করেছে (সর্বোচ্চ ৳২৫,০০০)';
    if (amt > curBalance) {
      return `অপর্যাপ্ত অ্যাকাউন্ট ব্যালেন্স! আপনার বর্তমান ব্যালেন্স ৳${curBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    }
    const min = isCashOut === 1 ? 50 : 10;
    if (amt < min) return `সর্বনিম্ন লেনদেন পরিমাণ ৳${min}`;
    return null;
  };

  const validationError = getValidationError(currentAmount, formData.is_cash_out, balance);
  const isPinValid = pin.length === 4;
  const isSubmitDisabled = loading || validationError !== null || !isPinValid;

  // Replenish Demo Balance (+৳20,000)
  const handleTopUp = () => {
    setBalance((prev) => {
      const updated = prev + 20000;
      if (typeof window !== 'undefined') {
        localStorage.setItem(LS_BALANCE_KEY, updated.toString());
      }
      return updated;
    });
  };

  // Deduct Balance on Success
  const deductBalance = (amountToDeduct: number) => {
    setBalance((prev) => {
      const updated = Math.max(prev - amountToDeduct, 0);
      if (typeof window !== 'undefined') {
        localStorage.setItem(LS_BALANCE_KEY, updated.toString());
      }
      return updated;
    });
  };

  // Quick Amount Chips: Clamped to balance and daily limit
  const handleChipClick = (exactAmount: number) => {
    setActiveScenario('custom');
    const clampedAmount = Math.min(exactAmount, Math.min(balance, MAX_DAILY_LIMIT));
    setFormData((prev) => ({
      ...prev,
      txn_amount: clampedAmount > 0 ? clampedAmount : exactAmount,
    }));
  };

  // Reset Amount to Default ৳500
  const handleResetAmount = () => {
    setActiveScenario('custom');
    setFormData((prev) => ({
      ...prev,
      txn_amount: DEFAULT_AMOUNT,
    }));
  };

  // Preset Scenario Loader
  const loadScenario = (scenarioKey: string) => {
    setActiveScenario(scenarioKey);
    let scenarioData: TxnFormData;

    if (scenarioKey === 'scenario-1') {
      scenarioData = {
        txn_amount: 500,
        hour_of_day: 14,
        device_change_count_30d: 0,
        velocity_last_1h: 1,
        agent_distance_km: 1.2,
        failed_pin_attempts_24h: 0,
        is_cash_out: 0,
      };
    } else if (scenarioKey === 'scenario-2') {
      scenarioData = {
        txn_amount: 25000,
        hour_of_day: 3,
        device_change_count_30d: 2,
        velocity_last_1h: 6,
        agent_distance_km: 18.5,
        failed_pin_attempts_24h: 3,
        is_cash_out: 1,
      };
    } else {
      scenarioData = {
        txn_amount: 18000,
        hour_of_day: 2,
        device_change_count_30d: 1,
        velocity_last_1h: 4,
        agent_distance_km: 8.0,
        failed_pin_attempts_24h: 1,
        is_cash_out: 1,
      };
    }

    // Ensure balance sufficiency for test presets
    if (balance < scenarioData.txn_amount) {
      const replenished = Math.max(ACCOUNT_INITIAL_BALANCE, scenarioData.txn_amount + 10000);
      setBalance(replenished);
      if (typeof window !== 'undefined') {
        localStorage.setItem(LS_BALANCE_KEY, replenished.toString());
      }
    }

    setFormData(scenarioData);
    setOtpVerified(false);
    setRecoveryMode(false);
    setRecoverySuccess(false);
    assessRisk(scenarioData, true);
  };

  // Live Telemetry Slider Adjustment
  const handleTelemetryChange = (field: keyof TxnFormData, value: number) => {
    setActiveScenario('custom');
    const updated = { ...formData, [field]: value };
    setFormData(updated);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      assessRisk(updated, false);
    }, 250);
  };

  // Core Evaluation Handler with Defensive API & Fallback Logic
  const assessRisk = async (overrideData?: TxnFormData, openModalOnComplete = false) => {
    const dataToAssess = overrideData || formData;
    setLoading(true);
    const startTime = performance.now();

    try {
      const response = await fetch(API_ASSESS_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dataToAssess),
        signal: AbortSignal.timeout(4000),
      });

      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);

      if (response.ok && response.status === 200) {
        let payload: any = null;
        try {
          const text = await response.text();
          if (text) payload = JSON.parse(text);
        } catch {
          payload = null;
        }

        if (
          payload &&
          typeof payload.risk_score === 'number' &&
          Array.isArray(payload.key_risk_drivers) &&
          typeof payload.recommended_action === 'string'
        ) {
          const parsedResult: RiskAssessmentResult = {
            risk_score: Number(payload.risk_score) || 0,
            risk_level: String(payload.risk_level || 'LOW'),
            recommended_action: String(payload.recommended_action || 'APPROVE'),
            key_risk_drivers: payload.key_risk_drivers.map((d: any) => ({
              feature: String(d?.feature || 'feature'),
              impact: Number(d?.impact) || 0,
            })),
            narrative: String(
              payload.narrative || 'Transaction evaluated. Baseline security markers verified.'
            ),
            inference_time_ms: payload.inference_time_ms || elapsed,
          };

          setResult(parsedResult);
          setBackendOnline(true);
          const assessedTime = new Date().toLocaleTimeString();
          setLastAssessedAt(assessedTime);

          if (openModalOnComplete) {
            setShowModal(true);
            setOtpVerified(false);
            setRecoveryMode(false);
            setRecoverySuccess(false);

            if (parsedResult.recommended_action === 'APPROVE') {
              deductBalance(dataToAssess.txn_amount);
            }
          }
          return;
        }
      }
      throw new Error(`HTTP ${response.status}`);
    } catch {
      // Client-side fallback mirroring LightGBM model weights
      const elapsed = Math.round(performance.now() - startTime);
      setLatencyMs(elapsed);
      setBackendOnline(false);

      let logit = -4.25;
      const isHighAmount = (dataToAssess.txn_amount || 0) > 15000;
      const isMidnight = (dataToAssess.hour_of_day || 0) >= 1 && (dataToAssess.hour_of_day || 0) <= 4;
      const isMidnightSpike = isMidnight && (dataToAssess.velocity_last_1h || 0) >= 3;
      const isMultiDevice = (dataToAssess.device_change_count_30d || 0) >= 2;
      const isPinFail = (dataToAssess.failed_pin_attempts_24h || 0) >= 2;

      if (isHighAmount) logit += 3.2;
      if (isMidnight) logit += 2.6;
      if (isMidnightSpike) logit += 2.5;
      if (isMultiDevice) logit += 2.75;
      if (isPinFail) logit += 3.1;
      if (dataToAssess.is_cash_out === 1) logit += 1.25;
      if ((dataToAssess.velocity_last_1h || 0) >= 4) logit += 1.15;
      logit += 0.04 * Math.min(dataToAssess.agent_distance_km || 0, 30);

      const prob = 1 / (1 + Math.exp(-logit));
      const score = Math.round(prob * 1000) / 10;

      const rawDrivers = [
        { feature: 'txn_amount', impact: isHighAmount ? 3.099 : -0.75 },
        { feature: 'failed_pin_attempts_24h', impact: isPinFail ? 2.753 : -0.39 },
        { feature: 'device_change_count_30d', impact: isMultiDevice ? 2.149 : -0.34 },
        { feature: 'hour_of_day', impact: isMidnight ? 2.451 : -0.25 },
        { feature: 'velocity_last_1h', impact: (dataToAssess.velocity_last_1h || 0) >= 4 ? 1.42 : -0.15 },
        { feature: 'is_cash_out', impact: dataToAssess.is_cash_out === 1 ? 1.12 : -0.52 },
      ];
      const sortedDrivers = rawDrivers
        .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
        .slice(0, 3);
      const topDriversStr = sortedDrivers.map((d) => d.feature).join(', ');

      let action = 'APPROVE';
      let level = 'LOW';
      let narrative =
        'Transaction conforms to expected baseline behavior. Low anomaly probability across biometric and velocity signals.';

      if (score >= 75) {
        action = 'BLOCK_IMMEDIATELY';
        level = 'HIGH';
        narrative = `Critical risk detected. Severe deviation driven by ${topDriversStr}. Transaction halted immediately; step-up verification or manual triage required.`;
      } else if (score >= 40) {
        action = 'STEP_UP_2FA';
        level = 'MEDIUM';
        narrative = `Moderate risk variance identified due to elevated ${topDriversStr}. Secondary biometric or SMS OTP challenge prompted to account holder.`;
      }

      setResult({
        risk_score: score,
        risk_level: level,
        recommended_action: action,
        key_risk_drivers: sortedDrivers,
        narrative,
        inference_time_ms: elapsed,
      });
      const assessedTime = new Date().toLocaleTimeString();
      setLastAssessedAt(assessedTime);

      if (openModalOnComplete) {
        setShowModal(true);
        setOtpVerified(false);
        setRecoveryMode(false);
        setRecoverySuccess(false);

        if (action === 'APPROVE') {
          deductBalance(dataToAssess.txn_amount);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  // Status Styling Logic
  const getStatusTheme = (action: string) => {
    switch (action) {
      case 'BLOCK_IMMEDIATELY':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          cardBorder: 'border-red-500',
          text: 'text-red-700',
          badgeBg: 'bg-red-600 text-white',
          dialColor: '#EF4444',
          statusIcon: ShieldAlert,
          bnStatus: 'তাত্ক্ষণিক লেনদেন স্থগিত (BLOCK)',
          description: 'গুরুতর জালিয়াতির ঝুঁকি সনাক্ত হয়েছে। সেন্ট্রাল গভর্নেন্সের মাধ্যমে লেনদেন স্থগিত করা হলো।',
        };
      case 'STEP_UP_2FA':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          cardBorder: 'border-amber-500',
          text: 'text-amber-700',
          badgeBg: 'bg-amber-500 text-white',
          dialColor: '#F59E0B',
          statusIcon: AlertTriangle,
          bnStatus: 'দ্বি-স্তর যাচাইকরণ আবশ্যক (STEP-UP 2FA)',
          description: 'অস্বাভাবিক লেনদেন প্যাটার্ন। গ্রাহকের ডিভাইসে বায়োমেট্রিক বা এসএমএস ওটিপি চ্যালেঞ্জ প্রেরণ করা হয়েছে।',
        };
      default:
        return {
          bg: 'bg-emerald-50',
          border: 'border-emerald-200',
          cardBorder: 'border-emerald-500',
          text: 'text-emerald-700',
          badgeBg: 'bg-emerald-600 text-white',
          dialColor: '#10B981',
          statusIcon: ShieldCheck,
          bnStatus: 'অনুমোদিত ও সম্পূর্ণ নিরাপদ (APPROVE)',
          description: 'স্বাভাবিক লেনদেন মানদণ্ডে উত্তীর্ণ। তাত্ক্ষণিক ফান্ড ট্রান্সফার প্রক্রিয়া অব্যাহত রয়েছে।',
        };
    }
  };

  const currentStatus = getStatusTheme(result?.recommended_action || 'APPROVE');
  const StatusIcon = currentStatus.statusIcon;

  // SVG Gauge calculations
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  const rawScore = Number(result?.risk_score) || 0;
  const scoreClamped = Math.min(Math.max(rawScore, 0), 100);
  const strokeDashoffset = circumference - (scoreClamped / 100) * circumference;

  // OTP Verification for 2FA Challenge
  const handleVerify2FAOtp = () => {
    setVerifyingOtp(true);
    setTimeout(() => {
      setVerifyingOtp(false);
      setOtpVerified(true);
      deductBalance(formData.txn_amount);
    }, 500);
  };

  // Self-Service Recovery Execution
  const handleExecuteRecovery = () => {
    setRecovering(true);
    setTimeout(() => {
      setRecovering(false);
      setRecoverySuccess(true);
      deductBalance(formData.txn_amount);

      const resetTelemetry = { ...formData, failed_pin_attempts_24h: 0 };
      setFormData(resetTelemetry);
      assessRisk(resetTelemetry, false);
    }, 600);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setRecoveryMode(false);
    setRecoverySuccess(false);
    setOtpVerified(false);
  };

  return (
    <div className="min-h-screen bg-[#F4F6F8] text-slate-800 flex flex-col font-sans">
      
      {/* 1. Header Bar */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-50 px-4 md:px-8 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          <div className="flex items-center gap-3">
            <div className="h-10 px-3 bg-[#FFC800] rounded-xl flex items-center justify-center shadow-sm">
              <span className="font-black text-[#063254] tracking-tight text-xl">upay</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-[#063254] tracking-tight leading-none">
                  RiskIntel <span className="text-[#063254] font-medium">| Trust &amp; Risk Intelligence</span>
                </h1>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#063254] text-white">
                  Track 01
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                UCB Fintech Ltd. • Real-time AI Fraud Scoring &amp; SHAP Governance
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-600">
              <Server className="h-3.5 w-3.5 text-slate-500" />
              <span className="hidden sm:inline text-slate-500">Backend:</span>
              {backendOnline === true ? (
                <span className="flex items-center gap-1.5 font-bold text-emerald-600">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  FastAPI Live
                </span>
              ) : backendOnline === false ? (
                <span className="flex items-center gap-1.5 font-bold text-amber-600" title="Running local client-side ML simulation">
                  <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                  Simulation Fallback
                </span>
              ) : (
                <span className="flex items-center gap-1.5 font-medium text-slate-500">
                  <RefreshCw className="h-3 w-3 animate-spin text-slate-500" />
                  Connecting...
                </span>
              )}
            </div>

            {latencyMs !== null && (
              <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700">
                <Activity className="h-3.5 w-3.5 text-[#063254]" />
                <span className="text-slate-500">Inference:</span>
                <span className="font-mono font-bold text-[#063254]">{latencyMs} ms</span>
              </div>
            )}
          </div>

        </div>
      </header>

      {/* 2. Evaluator Sandbox Toolbar */}
      <section className="bg-white border-b border-slate-200 shadow-sm px-4 md:px-8 py-3">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-100 text-[#063254]">
              <Sparkles className="h-4 w-4 text-[#063254]" />
            </div>
            <div>
              <span className="text-xs font-bold text-[#063254] uppercase tracking-wider block">
                Evaluator Sandbox Toolbar
              </span>
              <span className="text-[11px] text-slate-500">
                1-Click presets sync phone inputs, telemetry sliders, and trigger in-app decision modal:
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => loadScenario('scenario-1')}
              className={`flex-1 sm:flex-initial px-3.5 py-2 rounded-xl text-left border transition-all flex items-center gap-2 shadow-sm cursor-pointer ${
                activeScenario === 'scenario-1'
                  ? 'bg-emerald-50 border-emerald-500 text-emerald-900 ring-2 ring-emerald-400 font-bold'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300'
              }`}
            >
              <ShieldCheck className="h-4 w-4 text-emerald-600 flex-shrink-0" />
              <div>
                <div className="text-xs font-bold flex items-center gap-1.5">
                  Normal P2P
                  {activeScenario === 'scenario-1' && <Check className="h-3 w-3 text-emerald-600" />}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">৳500 • Low Risk</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => loadScenario('scenario-2')}
              className={`flex-1 sm:flex-initial px-3.5 py-2 rounded-xl text-left border transition-all flex items-center gap-2 shadow-sm cursor-pointer ${
                activeScenario === 'scenario-2'
                  ? 'bg-red-50 border-red-500 text-red-900 ring-2 ring-red-400 font-bold'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300'
              }`}
            >
              <AlertTriangle className="h-4 w-4 text-red-600 flex-shrink-0" />
              <div>
                <div className="text-xs font-bold flex items-center gap-1.5">
                  ATO Attack
                  {activeScenario === 'scenario-2' && <Check className="h-3 w-3 text-red-600" />}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">৳25,000 • Critical Risk</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => loadScenario('scenario-3')}
              className={`flex-1 sm:flex-initial px-3.5 py-2 rounded-xl text-left border transition-all flex items-center gap-2 shadow-sm cursor-pointer ${
                activeScenario === 'scenario-3'
                  ? 'bg-amber-50 border-amber-500 text-amber-900 ring-2 ring-amber-400 font-bold'
                  : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300'
              }`}
            >
              <Fingerprint className="h-4 w-4 text-amber-600 flex-shrink-0" />
              <div>
                <div className="text-xs font-bold flex items-center gap-1.5">
                  Midnight Cashout
                  {activeScenario === 'scenario-3' && <Check className="h-3 w-3 text-amber-600" />}
                </div>
                <div className="text-[10px] text-slate-500 font-mono">৳18,000 • Midnight Spikes</div>
              </div>
            </button>
          </div>

        </div>
      </section>

      {/* 3. Main Dual-Column Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 lg:p-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

          {/* ========================================================== */}
          {/* LEFT SCREEN: 100% Authentic Mobile App Simulator           */}
          {/* ========================================================== */}
          <section className="lg:col-span-5 flex flex-col items-center">
            <div className="w-full max-w-md bg-white rounded-[2.5rem] shadow-2xl border-4 border-slate-800 overflow-hidden relative select-none">
              
              <div className="w-full bg-[#F4F6F8] flex flex-col relative min-h-[640px]">
                
                {/* Feedback Modal Overlay */}
                <TransactionFeedbackModal
                  isOpen={showModal}
                  result={result}
                  formData={formData}
                  balance={balance}
                  onClose={handleCloseModal}
                  on2FAVerify={handleVerify2FAOtp}
                  onSelfServiceRecovery={handleExecuteRecovery}
                  verifyingOtp={verifyingOtp}
                  otpVerified={otpVerified}
                  recoveryMode={recoveryMode}
                  recovering={recovering}
                  recoverySuccess={recoverySuccess}
                  setRecoveryMode={setRecoveryMode}
                />

                {/* Top Status Bar */}
                <div className="bg-[#FFC800] px-6 pt-3 pb-1 flex items-center justify-between text-[#063254] font-semibold text-xs">
                  <span className="font-bold tracking-tight">9:41</span>
                  <div className="w-20 h-4 bg-[#063254] rounded-full mx-auto -mt-1 opacity-20"></div>
                  <div className="flex items-center gap-1.5">
                    <Signal className="h-3 w-3" />
                    <Wifi className="h-3 w-3" />
                    <Battery className="h-3.5 w-3.5" />
                  </div>
                </div>

                {/* Yellow upay App Header */}
                <div className="bg-[#FFC800] px-4 pt-2 pb-4 text-[#063254] flex flex-col gap-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="h-10 w-10 rounded-full bg-white text-[#063254] font-black flex items-center justify-center shadow-sm text-sm border border-amber-200">
                        HB
                      </div>
                      <div>
                        <h2 className="text-sm font-bold leading-tight text-[#063254]">
                          Homanur Bagum
                        </h2>
                        <span className="text-[11px] font-mono text-[#063254]/80">
                          01303069631
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-full bg-white/40 hover:bg-white/60 flex items-center justify-center text-[#063254] transition cursor-pointer">
                        <Bell className="h-4 w-4" />
                      </div>
                      <span className="font-black text-xl text-[#063254] tracking-tight">
                        upay
                      </span>
                    </div>
                  </div>

                  {/* Balance Pill & Reload Demo Funds */}
                  <div className="flex items-center gap-2 mt-0.5">
                    <button
                      type="button"
                      onClick={() => setShowBalance(!showBalance)}
                      className="px-3.5 py-1.5 bg-white hover:bg-amber-50 rounded-full text-xs font-bold text-[#063254] shadow-sm flex items-center gap-1.5 transition active:scale-95 border border-amber-200/60 cursor-pointer"
                    >
                      {showBalance ? (
                        <>
                          <EyeOff className="h-3.5 w-3.5 text-[#063254]" />
                          <span>৳ {balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                        </>
                      ) : (
                        <>
                          <Eye className="h-3.5 w-3.5 text-[#063254]" />
                          <span>ট্যাপ করে ব্যালেন্স দেখুন</span>
                        </>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={handleTopUp}
                      title="ডেমো ব্যালেন্স রিচার্জ করুন (+৳২০,০০০)"
                      className="px-2.5 py-1.5 bg-[#063254] hover:bg-[#08416C] text-[#FFC800] rounded-full text-xs font-bold shadow-sm flex items-center gap-1 transition active:scale-95 cursor-pointer"
                    >
                      <PlusCircle className="h-3.5 w-3.5" />
                      <span>+৳২০,০০০</span>
                    </button>
                  </div>
                </div>

                {/* Mobile Screen Form Body */}
                <div className="p-4 space-y-3.5 overflow-y-auto">
                  
                  {/* Channel Switcher */}
                  <div className="bg-slate-200/70 p-1 rounded-2xl flex items-center">
                    <button
                      type="button"
                      onClick={() => {
                        setActiveScenario('custom');
                        setFormData((prev) => ({ ...prev, is_cash_out: 0 }));
                      }}
                      className={`flex-1 py-2 rounded-xl text-xs flex items-center justify-center gap-1.5 transition cursor-pointer ${
                        formData.is_cash_out === 0
                          ? 'bg-[#063254] text-white shadow-sm font-medium'
                          : 'text-slate-600 hover:text-slate-900 font-normal bg-transparent'
                      }`}
                    >
                      <Send className="h-3.5 w-3.5" />
                      <span>সেন্ড মানি (P2P)</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setActiveScenario('custom');
                        setFormData((prev) => ({ ...prev, is_cash_out: 1 }));
                      }}
                      className={`flex-1 py-2 rounded-xl text-xs flex items-center justify-center gap-1.5 transition cursor-pointer ${
                        formData.is_cash_out === 1
                          ? 'bg-[#063254] text-white shadow-sm font-medium'
                          : 'text-slate-600 hover:text-slate-900 font-normal bg-transparent'
                      }`}
                    >
                      <Building2 className="h-3.5 w-3.5" />
                      <span>ক্যাশ আউট (Agent)</span>
                    </button>
                  </div>

                  {/* Recipient Details */}
                  <div className="bg-white rounded-2xl p-3.5 border border-slate-200 shadow-sm flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-[#063254]/10 text-[#063254] flex items-center justify-center font-bold text-xs">
                        {formData.is_cash_out === 1 ? 'AG' : 'RX'}
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-[#063254]">
                            {formData.is_cash_out === 1 ? 'এজেন্ট ক্যাশ-আউট পয়েন্ট' : 'প্রাপক: 01812-345678'}
                          </span>
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                        </div>
                        <p className="text-[11px] text-slate-500 font-mono">
                          {formData.is_cash_out === 1 ? 'upay Verified Agent (#88219)' : 'upay Verified User (MFS)'}
                        </p>
                      </div>
                    </div>

                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      সক্রিয়
                    </span>
                  </div>

                  {/* Transaction Submission Form */}
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (!isSubmitDisabled) {
                        assessRisk(undefined, true);
                      }
                    }}
                    className="space-y-3.5"
                  >
                    
                    {/* Amount Input with Chips */}
                    <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm space-y-2.5">
                      <div className="flex items-center justify-between">
                        <label htmlFor="amount-input" className="text-xs font-bold text-[#063254]">
                          পরিমাণ (টাকা)
                        </label>
                        <span className="text-[10px] text-slate-500 font-medium">
                          উপলব্ধ ব্যালেন্স: ৳{balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </span>
                      </div>

                      <div className="relative flex items-center">
                        <span className="text-2xl font-black text-[#063254] mr-2">৳</span>
                        <input
                          id="amount-input"
                          type="number"
                          min={minAmount}
                          max={MAX_DAILY_LIMIT}
                          step="any"
                          placeholder="0"
                          value={formData.txn_amount === 0 ? '' : formData.txn_amount}
                          onChange={(e) => {
                            setActiveScenario('custom');
                            const val = e.target.value;
                            if (val === '') {
                              setFormData((prev) => ({ ...prev, txn_amount: 0 }));
                            } else {
                              const parsed = parseFloat(val);
                              if (!isNaN(parsed)) {
                                setFormData((prev) => ({ ...prev, txn_amount: parsed }));
                              }
                            }
                          }}
                          className={`w-full text-2xl font-black font-mono text-[#063254] bg-transparent outline-none border-b-2 pb-1 transition ${
                            validationError ? 'border-red-400 focus:border-red-500' : 'border-slate-200 focus:border-[#FFC800]'
                          }`}
                          required
                        />
                      </div>

                      {validationError ? (
                        <div className="flex items-center gap-1.5 text-red-600 font-bold text-[11px] pt-0.5">
                          <AlertTriangle className="h-3.5 w-3.5 flex-shrink-0" />
                          <span>{validationError}</span>
                        </div>
                      ) : (
                        <p className="text-[10px] text-slate-400 font-medium pt-0.5">
                          {formData.is_cash_out === 1
                            ? 'লেনদেনের সীমা: ৳৫০ - ৳২৫,০০০ | দৈনিক সর্বোচ্চ সীমা: ৳২৫,০০০'
                            : 'লেনদেনের সীমা: ৳১০ - ৳২৫,০০০ | দৈনিক সর্বোচ্চ সীমা: ৳২৫,০০০'}
                        </p>
                      )}

                      {/* Quick Amount Chips */}
                      <div className="flex items-center gap-1.5 pt-1">
                        {[500, 2000, 10000, 25000].map((amt) => (
                          <button
                            key={amt}
                            type="button"
                            onClick={() => handleChipClick(amt)}
                            className="flex-1 py-1 rounded-lg text-xs font-bold font-mono transition border bg-slate-50 text-slate-700 border-slate-200 hover:bg-amber-100 hover:border-amber-300 hover:text-[#063254] active:scale-95 cursor-pointer"
                          >
                            +৳{amt.toLocaleString()}
                          </button>
                        ))}
                        <button
                          type="button"
                          onClick={handleResetAmount}
                          title="পরিমাণ রিসেট করুন (৳৫০০)"
                          className="px-2 py-1 rounded-lg text-xs font-semibold text-slate-500 border border-slate-200 hover:bg-amber-50 hover:text-[#063254] transition cursor-pointer"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Reference Input */}
                    <div className="bg-white rounded-2xl p-3 border border-slate-200 shadow-sm flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-500">রেফারেন্স (ঐচ্ছিক):</span>
                      <input
                        type="text"
                        placeholder="যেমন: মাসিক খরচ, কেনাকাটা"
                        value={referenceNote}
                        onChange={(e) => setReferenceNote(e.target.value)}
                        className="text-xs font-medium text-slate-700 text-right outline-none bg-transparent w-48 placeholder-slate-300"
                      />
                    </div>

                    {/* Realistic MFS 4-Digit PIN Input Field */}
                    <div className="bg-white rounded-2xl p-3 border border-slate-200 shadow-sm space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label htmlFor="mfs-pin" className="text-xs font-bold text-[#063254] flex items-center gap-1.5">
                          <Lock className="h-3.5 w-3.5 text-[#063254]" />
                          <span>আপনার upay পিন নম্বর দিন</span>
                        </label>
                        <span className="text-[10px] text-slate-400 font-mono">৪ সংখ্যা</span>
                      </div>
                      <input
                        id="mfs-pin"
                        type="password"
                        maxLength={4}
                        value={pin}
                        onChange={(e) => {
                          const digitsOnly = e.target.value.replace(/\D/g, '').slice(0, 4);
                          setPin(digitsOnly);
                        }}
                        placeholder="••••"
                        className="w-full py-2 px-3 text-center text-lg font-black font-mono tracking-widest text-[#063254] bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-[#FFC800] focus:bg-white transition"
                        required
                      />
                      {pin.length > 0 && pin.length < 4 && (
                        <p className="text-[10px] text-red-500 font-medium text-center">
                          ৪ সংখ্যার সঠিক পিন নম্বর প্রদান করুন
                        </p>
                      )}
                    </div>

                    {/* Submit Button */}
                    <button
                      type="submit"
                      disabled={isSubmitDisabled}
                      className={`w-full py-3.5 px-4 rounded-2xl font-bold text-sm tracking-wide transition flex items-center justify-center gap-2 ${
                        isSubmitDisabled
                          ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                          : 'bg-[#063254] hover:bg-[#08416C] text-white shadow-lg shadow-[#063254]/25 active:scale-[0.98] cursor-pointer'
                      }`}
                    >
                      {loading ? (
                        <>
                          <RefreshCw className="h-4 w-4 animate-spin text-[#FFC800]" />
                          <span>যাচাই করা হচ্ছে (LightGBM &amp; SHAP)...</span>
                        </>
                      ) : (
                        <>
                          <Send className={`h-4 w-4 ${isSubmitDisabled ? 'text-slate-400' : 'text-[#FFC800]'}`} />
                          <span>{formData.is_cash_out === 1 ? 'ক্যাশ আউট নিশ্চিত করুন' : 'টাকা পাঠান / নিশ্চিত করুন'}</span>
                        </>
                      )}
                    </button>
                  </form>

                </div>

                {/* Bottom App Navigation Bar */}
                <div className="bg-white border-t border-slate-200 px-4 py-2 flex items-center justify-between relative mt-auto">
                  <div className="flex flex-col items-center text-[#063254] gap-0.5 cursor-pointer">
                    <Home className="h-4 w-4 stroke-[2.5]" />
                    <span className="text-[9px] font-bold">হোম</span>
                  </div>

                  <div className="flex flex-col items-center text-slate-400 gap-0.5 cursor-pointer hover:text-slate-600">
                    <User className="h-4 w-4" />
                    <span className="text-[9px]">অ্যাকাউন্ট</span>
                  </div>

                  {/* Raised Bangla QR Button */}
                  <div className="flex flex-col items-center -mt-6">
                    <div className="h-12 w-12 rounded-full bg-[#FFC800] border-4 border-white shadow-md flex items-center justify-center text-[#063254] hover:scale-105 active:scale-95 transition cursor-pointer">
                      <QrCode className="h-6 w-6 stroke-[2.2]" />
                    </div>
                    <span className="text-[9px] font-bold text-[#063254] mt-0.5">বাংলা QR</span>
                  </div>

                  <div className="flex flex-col items-center text-slate-400 gap-0.5 cursor-pointer hover:text-slate-600">
                    <History className="h-4 w-4" />
                    <span className="text-[9px]">হিস্টরি</span>
                  </div>

                  <div className="flex flex-col items-center text-slate-400 gap-0.5 cursor-pointer hover:text-slate-600">
                    <Menu className="h-4 w-4" />
                    <span className="text-[9px]">মেন্যু</span>
                  </div>
                </div>

                <div className="bg-white pb-1 pt-0.5 flex justify-center">
                  <div className="w-28 h-1 bg-slate-300 rounded-full"></div>
                </div>

              </div>
            </div>
            <p className="text-xs text-slate-400 mt-2 font-medium">upay Android/iOS Mobile App Simulator</p>
          </section>

          {/* ========================================================== */}
          {/* RIGHT SCREEN: Telemetry Inspector & AI Shield Console      */}
          {/* ========================================================== */}
          <section className="lg:col-span-7 space-y-6">

            {/* Inspector Card */}
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-md space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-slate-100 text-[#063254]">
                    <Sliders className="h-5 w-5 text-[#063254]" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#063254]">
                      সিমুলেটেড নেটওয়ার্ক ও ডিভাইস টেলিমেট্রি (Live Telemetry Inspector)
                    </h3>
                    <p className="text-[11px] text-slate-500">
                      স্লাইডার পরিবর্তন করলে রিয়েল-টাইমে ব্যাকএন্ড এআই স্কোর ও SHAP ড্রাইভার আপডেট হবে
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => assessRisk(undefined, false)}
                  disabled={loading}
                  className="px-3 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-300 text-[#063254] font-bold text-xs flex items-center gap-1.5 transition active:scale-95 cursor-pointer self-start sm:self-auto disabled:opacity-60"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
                  <span>মডেল মূল্যায়ন (Evaluate)</span>
                </button>
              </div>

              {/* Sliders Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                
                {/* 1. Hour of Day */}
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#063254] flex items-center gap-1.5">
                      <Clock className="h-3.5 w-3.5 text-slate-500" />
                      লেনদেনের সময় (Hour)
                    </span>
                    <span className="font-mono font-bold text-[#063254]">
                      {formData.hour_of_day.toString().padStart(2, '0')}:00 ({formData.hour_of_day < 12 ? 'AM' : 'PM'})
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="23"
                    step="1"
                    value={formData.hour_of_day}
                    onChange={(e) => handleTelemetryChange('hour_of_day', parseInt(e.target.value) || 0)}
                    className="w-full accent-[#063254] cursor-pointer"
                  />
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-slate-400">00:00 (মধ্যরাত)</span>
                    {formData.hour_of_day >= 1 && formData.hour_of_day <= 4 ? (
                      <span className="text-red-600 font-bold">⚠️ মধ্যরাত উচ্চ-ঝুঁকি উইন্ডো (01-04)</span>
                    ) : (
                      <span className="text-slate-400">23:00</span>
                    )}
                  </div>
                </div>

                {/* 2. Transaction Velocity */}
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#063254] flex items-center gap-1.5">
                      <Activity className="h-3.5 w-3.5 text-slate-500" />
                      ১ ঘণ্টার ফ্রিকোয়েন্সি (Velocity)
                    </span>
                    <span className="font-mono font-bold text-[#063254]">
                      {formData.velocity_last_1h} txns / hr
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="15"
                    step="1"
                    value={formData.velocity_last_1h}
                    onChange={(e) => handleTelemetryChange('velocity_last_1h', parseInt(e.target.value) || 0)}
                    className="w-full accent-[#063254] cursor-pointer"
                  />
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-slate-400">০ (স্বাভাবিক)</span>
                    {formData.velocity_last_1h >= 4 ? (
                      <span className="text-red-600 font-bold">⚠️ উচ্চ লেনদেন ফ্রিকোয়েন্সি স্পাইক</span>
                    ) : (
                      <span className="text-slate-400">১৫+ লেনদেন</span>
                    )}
                  </div>
                </div>

                {/* 3. Device Changes */}
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#063254] flex items-center gap-1.5">
                      <Smartphone className="h-3.5 w-3.5 text-slate-500" />
                      ডিভাইস পরিবর্তন (৩০ দিন)
                    </span>
                    <span className="font-mono font-bold text-[#063254]">
                      {formData.device_change_count_30d} switches
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="1"
                    value={formData.device_change_count_30d}
                    onChange={(e) => handleTelemetryChange('device_change_count_30d', parseInt(e.target.value) || 0)}
                    className="w-full accent-[#063254] cursor-pointer"
                  />
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-slate-400">০ পরিবর্তন</span>
                    {formData.device_change_count_30d >= 2 ? (
                      <span className="text-red-600 font-bold">⚠️ SIM Swap / ATO ঝুঁকি</span>
                    ) : (
                      <span className="text-slate-400">৫ টি ডিভাইস</span>
                    )}
                  </div>
                </div>

                {/* 4. Failed PIN Attempts */}
                <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[#063254] flex items-center gap-1.5">
                      <Lock className="h-3.5 w-3.5 text-slate-500" />
                      ভুল পিন চেষ্টা (২৪ ঘণ্টা)
                    </span>
                    <span className="font-mono font-bold text-[#063254]">
                      {formData.failed_pin_attempts_24h} failures
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="1"
                    value={formData.failed_pin_attempts_24h}
                    onChange={(e) => handleTelemetryChange('failed_pin_attempts_24h', parseInt(e.target.value) || 0)}
                    className="w-full accent-[#063254] cursor-pointer"
                  />
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-slate-400">০ (সঠিক পিন)</span>
                    {formData.failed_pin_attempts_24h >= 2 ? (
                      <span className="text-red-600 font-bold">⚠️ ব্রুট-ফোর্স অ্যাটাক প্যাটার্ন</span>
                    ) : (
                      <span className="text-slate-400">৫ চেষ্টা</span>
                    )}
                  </div>
                </div>

              </div>

              {/* 5. Agent Distance */}
              <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#063254] flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-slate-500" />
                    এজেন্ট অথবা ইউজারের ভৌগোলিক দূরত্ব (Agent Distance)
                  </span>
                  <span className="font-mono font-bold text-[#063254]">
                    {formData.agent_distance_km.toFixed(1)} km
                  </span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="40"
                  step="0.5"
                  value={formData.agent_distance_km}
                  onChange={(e) => handleTelemetryChange('agent_distance_km', parseFloat(e.target.value) || 0.1)}
                  className="w-full accent-[#063254] cursor-pointer"
                />
                <div className="flex justify-between items-center text-[10px] text-slate-400">
                  <span>০.১ কিমি (কাছের এজেন্ট)</span>
                  <span>২০ কিমি</span>
                  <span>৪০ কিমি (অস্বাভাবিক দূরবর্তী)</span>
                </div>
              </div>
            </div>

            {/* AI Risk Shield & XAI Attribution Console */}
            <div className={`bg-white rounded-3xl border-2 ${currentStatus.cardBorder} p-6 md:p-8 shadow-xl transition-all duration-300 relative overflow-hidden`}>
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-[#063254]">
                    <ShieldAlert className="h-6 w-6 text-[#063254]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-black text-[#063254] tracking-tight">
                      upay Trust &amp; Risk AI Shield
                    </h2>
                    <p className="text-xs text-slate-500 font-medium">
                      ইনটেলিজেন্স ও গভর্নেন্স কনসোল • UCB Fintech Ltd.
                    </p>
                  </div>
                </div>

                {lastAssessedAt && (
                  <div className="flex items-center gap-1.5 self-start sm:self-auto px-3 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-mono">
                    <Clock className="h-3 w-3 text-slate-400" />
                    <span>যাচাইকৃত: {lastAssessedAt}</span>
                  </div>
                )}
              </div>

              {/* Gauge and Decision Badge */}
              <div className="py-6 flex flex-col sm:flex-row items-center justify-around gap-6">
                
                <div className="relative flex items-center justify-center">
                  <svg className="w-44 h-44 transform -rotate-90">
                    <circle
                      cx="88"
                      cy="88"
                      r={radius}
                      stroke="#E2E8F0"
                      strokeWidth="12"
                      fill="transparent"
                    />
                    <circle
                      cx="88"
                      cy="88"
                      r={radius}
                      stroke={currentStatus.dialColor}
                      strokeWidth="12"
                      strokeDasharray={circumference}
                      strokeDashoffset={strokeDashoffset}
                      strokeLinecap="round"
                      fill="transparent"
                      className="transition-all duration-700 ease-out"
                    />
                  </svg>

                  <div className="absolute flex flex-col items-center justify-center text-center">
                    <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400">
                      ঝুঁকি স্কোর (Risk)
                    </span>
                    <span className="text-4xl font-black font-mono tracking-tight text-[#063254] mt-0.5">
                      {rawScore.toFixed(1)}
                    </span>
                    <span className="text-[11px] font-bold text-slate-400">
                      / ১০০
                    </span>
                  </div>
                </div>

                <div className="flex flex-col items-center sm:items-start text-center sm:text-left gap-2 max-w-[280px]">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                    অটোমেটেড পলিসি সিদ্ধান্ত (Decision)
                  </span>

                  <div className={`px-4 py-2 rounded-xl font-bold font-mono text-sm tracking-wide uppercase shadow-md flex items-center gap-2 ${currentStatus.badgeBg}`}>
                    <StatusIcon className="h-4 w-4" />
                    <span>{result?.recommended_action || 'APPROVE'}</span>
                  </div>

                  <span className={`text-xs font-bold ${currentStatus.text}`}>
                    {currentStatus.bnStatus}
                  </span>

                  <p className="text-xs text-slate-600 leading-relaxed mt-1">
                    {currentStatus.description}
                  </p>
                </div>

              </div>

              {/* Narrative Briefing */}
              <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 md:p-5 space-y-1.5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#063254]">
                  <Info className="h-4 w-4 text-[#FFC800]" />
                  <span>অ্যানালিস্ট ইনভেস্টিগেশন ব্রিফিং (Narrative)</span>
                </div>
                <p className="text-xs md:text-sm text-slate-700 leading-relaxed font-sans">
                  {result?.narrative || 'রিয়েল-টাইম ট্রানজেকশন ডেটা প্রদান করে এআই ব্রিফিং পর্যবেক্ষণ করুন।'}
                </p>
              </div>

              {/* SHAP Feature Attribution */}
              <div className="mt-4 bg-slate-50 border border-slate-200 rounded-2xl p-4 md:p-5 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-wider text-[#063254] flex items-center gap-1.5">
                    <TrendingUp className="h-4 w-4 text-[#FFC800]" />
                    SHAP এক্সপ্লেইনেবিলিটি: শীর্ষ ৩ ঝুঁকি চালক (Local Drivers)
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">TreeExplainer XAI</span>
                </div>

                {Array.isArray(result?.key_risk_drivers) && result.key_risk_drivers.length > 0 ? (
                  <div className="space-y-3 pt-1">
                    {result.key_risk_drivers.map((driver, index) => {
                      const impactVal = Number(driver?.impact) || 0;
                      const isRiskElevating = impactVal > 0;
                      const absImpact = Math.abs(impactVal);
                      const barWidth = Math.min(Math.max((absImpact / 5.0) * 100, 15), 100);
                      const meta = FEATURE_META[driver.feature] || {
                        label: driver.feature,
                        bnLabel: driver.feature,
                        icon: Zap,
                      };
                      const DriverIcon = meta.icon;

                      return (
                        <div key={index} className="space-y-1 bg-white p-3 rounded-xl border border-slate-200">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-[#063254] flex items-center gap-1.5">
                              <DriverIcon className="h-3.5 w-3.5 text-slate-500" />
                              {meta.bnLabel} ({meta.label})
                            </span>
                            <span
                              className={`font-mono text-xs font-bold ${
                                isRiskElevating ? 'text-red-600' : 'text-emerald-600'
                              }`}
                            >
                              {impactVal > 0 ? `+${impactVal.toFixed(4)}` : impactVal.toFixed(4)}
                              <span className="text-[10px] text-slate-500 ml-1 font-sans">
                                {isRiskElevating ? '(ঝুঁকি বৃদ্ধি)' : '(ঝুঁকি হ্রাস)'}
                              </span>
                            </span>
                          </div>

                          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isRiskElevating
                                  ? 'bg-gradient-to-r from-amber-400 to-red-500'
                                  : 'bg-gradient-to-r from-emerald-400 to-teal-500'
                              }`}
                              style={{ width: `${barWidth}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">কোনো ড্রাইভার উপলব্ধ নেই।</p>
                )}
              </div>

              {/* Audit Badge */}
              <div className="mt-4 pt-4 border-t border-slate-200 grid grid-cols-3 gap-2 text-center text-xs">
                <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-200">
                  <span className="block text-[10px] text-slate-500 uppercase font-bold">মডেল আর্কিটেকচার</span>
                  <span className="text-xs font-mono font-bold text-[#063254] mt-0.5 block">
                    LightGBM (100 Trees)
                  </span>
                </div>
                <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-200">
                  <span className="block text-[10px] text-slate-500 uppercase font-bold">রেগুলেটরি কমপ্লায়েন্স</span>
                  <span className="text-xs font-bold text-emerald-700 mt-0.5 block">
                    বাংলাদেশ ব্যাংক MFS
                  </span>
                </div>
                <div className="bg-slate-50 rounded-xl p-2.5 border border-slate-200">
                  <span className="block text-[10px] text-slate-500 uppercase font-bold">অডিট রেকর্ড</span>
                  <span className="text-xs font-bold text-slate-700 mt-0.5 block">
                    Audit Trail Active
                  </span>
                </div>
              </div>

            </div>

          </section>

        </div>
      </main>

      {/* 4. Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white px-6 py-4 text-center text-xs text-slate-500">
        <p>
          RiskIntel upay &copy; {new Date().getFullYear()} UCB Fintech Ltd. &bull; Track 01: Trust &amp; Risk Intelligence &bull; Built with FastAPI, LightGBM, SHAP &amp; Next.js 14
        </p>
      </footer>

    </div>
  );
}

