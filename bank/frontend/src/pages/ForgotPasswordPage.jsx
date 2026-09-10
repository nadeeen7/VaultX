import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { forgotPassword, verifyOtp, resetPassword } from "../services/api.js";
import Alert from "../components/Alert.jsx";
import { ArrowRight, ArrowLeft, Shield, Mail, KeyRound, CheckCircle } from "lucide-react";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();

  // Step management: "email" → "otp" → "reset" → "done"
  const [step, setStep] = useState("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  // ── Step 1: Send OTP ──
  const handleSendOtp = async (e) => {
    e.preventDefault();
    setError("");
    if (!email.trim()) {
      setError("Please enter your email address");
      return;
    }

    setLoading(true);
    try {
      const res = await forgotPassword({ email: email.trim() });
      setSuccessMsg(res.data.message || "A verification code has been sent to your email.");
      setStep("otp");
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ── Step 2: Verify OTP ──
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError("");
    const otpString = otp.join("");
    if (otpString.length !== 6) {
      setError("Please enter the complete 6-digit code");
      return;
    }

    setLoading(true);
    try {
      const res = await verifyOtp({ email: email.trim(), otp: otpString });
      setResetToken(res.data.reset_token);
      setSuccessMsg("Code verified. Please set your new password.");
      setStep("reset");
    } catch (err) {
      setError(err.response?.data?.error || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ── Step 3: Reset Password ──
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      await resetPassword({
        email: email.trim(),
        reset_token: resetToken,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setStep("done");
    } catch (err) {
      setError(err.response?.data?.error || "Password reset failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // OTP input handler
  const handleOtpChange = (index, value) => {
    if (!/^\d*$/.test(value) && value !== "") return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    setError("");

    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.querySelector(`input[name="otp-${index + 1}"]`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.querySelector(`input[name="otp-${index - 1}"]`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (pastedData) {
      const newOtp = pastedData.split("").concat(Array(6).fill("")).slice(0, 6);
      setOtp(newOtp);
      // Focus the last filled input or the next empty one
      const focusIndex = Math.min(pastedData.length, 5);
      const nextInput = document.querySelector(`input[name="otp-${focusIndex}"]`);
      if (nextInput) nextInput.focus();
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12 bg-slate-50 dark:bg-slate-900">
      <div className="w-full max-w-md animate-slide-up">
        {/* Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-lg p-8">
          {/* Step 1: Email Entry */}
          {step === "email" && (
            <>
              <div className="text-center mb-8">
                <div className="w-12 h-12 bg-navy-800 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Mail className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Forgot password?</h1>
                <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">
                  Enter your email and we&apos;ll send you a verification code
                </p>
              </div>

              {error && <Alert type="error" message={error} onClose={() => setError("")} />}

              <form onSubmit={handleSendOtp} className="mt-6 space-y-4">
                <div>
                  <label className="label">Email address</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => { setEmail(e.target.value); setError(""); }}
                    required
                    className="input-field"
                    placeholder="john@example.com"
                    autoComplete="email"
                    autoFocus
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full !py-3 mt-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      Send Verification Code
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          )}

          {/* Step 2: OTP Verification */}
          {step === "otp" && (
            <>
              <div className="text-center mb-8">
                <div className="w-12 h-12 bg-navy-800 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <KeyRound className="w-6 h-6 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Enter verification code</h1>
                <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">
                  We sent a 6-digit code to <span className="font-medium text-gray-700 dark:text-gray-300">{email}</span>
                </p>
              </div>

              {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg("")} />}
              {error && <Alert type="error" message={error} onClose={() => setError("")} />}

              <form onSubmit={handleVerifyOtp} className="mt-6 space-y-4">
                {/* OTP inputs */}
                <div className="flex justify-center gap-2">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      name={`otp-${index}`}
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(index, e)}
                      onPaste={handleOtpPaste}
                      className="w-12 h-14 text-center text-lg font-bold input-field !px-0"
                      autoFocus={index === 0}
                    />
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full !py-3 mt-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      Verify Code
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              <button
                onClick={() => { setStep("email"); setError(""); setSuccessMsg(""); setOtp(["", "", "", "", "", ""]); }}
                className="flex items-center justify-center gap-2 w-full mt-4 text-sm text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Use a different email
              </button>
            </>
          )}

          {/* Step 3: Reset Password */}
          {step === "reset" && (
            <>
              <div className="text-center mb-8">
                <div className="w-12 h-12 bg-navy-800 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Set new password</h1>
                <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">
                  Choose a strong password for your account
                </p>
              </div>

              {successMsg && <Alert type="success" message={successMsg} onClose={() => setSuccessMsg("")} />}
              {error && <Alert type="error" message={error} onClose={() => setError("")} />}

              <form onSubmit={handleResetPassword} className="mt-6 space-y-4">
                <div>
                  <label className="label">New Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => { setNewPassword(e.target.value); setError(""); }}
                    required
                    className="input-field"
                    placeholder="Min. 8 characters"
                    autoComplete="new-password"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="label">Confirm Password</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => { setConfirmPassword(e.target.value); setError(""); }}
                    required
                    className="input-field"
                    placeholder="Re-enter password"
                    autoComplete="new-password"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full !py-3 mt-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Resetting...
                    </>
                  ) : (
                    <>
                      Reset Password
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          )}

          {/* Step 4: Success */}
          {step === "done" && (
            <>
              <div className="text-center mb-8">
                <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                </div>
                <h1 className="text-2xl font-bold text-navy-900 dark:text-white">Password reset successful</h1>
                <p className="text-sm text-gray-500 dark:text-slate-400 mt-1.5">
                  Your password has been updated. You can now sign in with your new password.
                </p>
              </div>

              <button
                onClick={() => navigate("/login")}
                className="btn-primary w-full !py-3 mt-4"
              >
                Back to Sign In
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}
        </div>

        {/* Security badge */}
        <div className="flex items-center justify-center gap-2 mt-6 text-gray-400 dark:text-slate-500">
          <Shield className="w-3.5 h-3.5" />
          <span className="text-xs font-medium">256-bit encrypted • Secure banking</span>
        </div>
      </div>
    </div>
  );
}
