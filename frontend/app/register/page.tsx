"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const { register, isLoading, error, clearError } = useAuth();

  const [formData, setFormData] = useState({
    email:     "",
    full_name: "",
    phone:     "",
    password:  "",
    password2: "",
    role:      "developer" as "developer" | "buyer",
  });
  const [showPassword,  setShowPassword]  = useState(false);
  const [showPassword2, setShowPassword2] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    clearError();
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Client-side password match check
    if (formData.password !== formData.password2) {
      return; // serializer will catch this too
    }

    await register(formData);
  }

  // ── Password strength indicator ───────────────────────────
  const passwordStrength = (() => {
    const p = formData.password;
    if (!p) return null;
    if (p.length < 8)  return { label: "Terlalu pendek", color: "var(--color-danger)",  width: "25%" };
    if (p.length < 10) return { label: "Lemah",          color: "var(--color-warning)", width: "50%" };
    if (!/[A-Z]/.test(p) || !/[0-9]/.test(p))
                       return { label: "Sedang",         color: "var(--color-warning)", width: "65%" };
    return               { label: "Kuat",           color: "var(--color-success)", width: "100%" };
  })();

  const passwordsMatch =
    formData.password2.length > 0 &&
    formData.password === formData.password2;

  return (
    <div className="min-h-screen bg-paper grid md:grid-cols-2">

      {/* ── Left — dark panel ── */}
      <div
        className="hidden md:flex flex-col justify-between p-12 relative overflow-hidden"
        style={{ backgroundColor: "var(--color-ink)" }}
      >
        <div className="relative z-10">
          <div style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 600, color: "white" }}>
            Rumah<span style={{ color: "var(--color-gold)" }}>Asri</span>
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Platform Properti
          </div>
        </div>
        <div className="absolute inset-0 opacity-[0.04]"
          style={{ backgroundImage: "linear-gradient(white 1px,transparent 1px),linear-gradient(90deg,white 1px,transparent 1px)", backgroundSize: "48px 48px" }}
        />

        {/* Feature list */}
        <div className="relative z-10 flex-1 flex items-center">
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {[
              { title: "Lacak konstruksi real-time",   desc: "Pantau setiap fase pembangunan dengan foto lapangan" },
              { title: "Manajemen pembayaran KPR",      desc: "BCA, BNI, BTN, Mandiri — semua dalam satu platform" },
              { title: "Portal pembeli eksklusif",      desc: "Pembeli bisa pantau rumah mereka kapan saja" },
              { title: "Laporan PDF & Excel",            desc: "Satu klik untuk laporan investor & keuangan" },
            ].map((f, i) => (
              <div key={i} style={{ display: "flex", gap: 14 }}>
                <CheckCircle2 size={18} style={{ color: "var(--color-gold)", flexShrink: 0, marginTop: 2 }}/>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "white", marginBottom: 2 }}>{f.title}</div>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", lineHeight: 1.5 }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10" style={{ fontSize: 12, color: "rgba(255,255,255,0.25)" }}>
          © 2026 RumahAsri · JasaPro · Jambi, Indonesia
        </div>
      </div>

      {/* ── Right — form ── */}
      <div className="flex items-center justify-center p-8 overflow-y-auto">
        <div className="w-full max-w-sm py-8">

          {/* Mobile logo */}
          <div className="md:hidden mb-8" style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 600, color: "var(--color-ink)" }}>
            Rumah<span style={{ color: "var(--color-accent)" }}>Asri</span>
          </div>

          <h1 style={{ fontSize: 24, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
            Buat akun baru
          </h1>
          <p style={{ fontSize: 13, color: "var(--color-ink-3)", marginBottom: 28 }}>
            Mulai kelola properti Anda bersama RumahAsri
          </p>

          {/* Error alert */}
          {error && (
            <div style={{
              display: "flex", alignItems: "flex-start", gap: 10,
              padding: "12px 14px", marginBottom: 20,
              backgroundColor: "var(--color-danger-light)",
              border: "1px solid rgba(185,28,28,0.2)",
              borderRadius: 6,
            }}>
              <AlertCircle size={15} style={{ color: "var(--color-danger)", flexShrink: 0, marginTop: 1 }}/>
              <span style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>

            {/* Role selector */}
            <div>
              <label className="form-label">Daftar sebagai</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                {[
                  { value: "developer", label: "Developer", desc: "Akses dasbor penuh" },
                  { value: "buyer",     label: "Pembeli",   desc: "Portal status unit" },
                ].map((r) => (
                  <button
                    key={r.value}
                    type="button"
                    onClick={() => { clearError(); setFormData(p => ({ ...p, role: r.value as "developer" | "buyer" })); }}
                    style={{
                      padding: "10px 12px", textAlign: "left",
                      border: formData.role === r.value
                        ? "1.5px solid var(--color-accent)"
                        : "1px solid rgba(14,13,11,0.12)",
                      borderRadius: 6,
                      backgroundColor: formData.role === r.value
                        ? "var(--color-accent-light)"
                        : "white",
                      cursor: "pointer", transition: "all 0.15s",
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 600, color: formData.role === r.value ? "var(--color-accent)" : "var(--color-ink)" }}>
                      {r.label}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--color-ink-3)", marginTop: 2 }}>
                      {r.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Full name */}
            <div>
              <label className="form-label">Nama Lengkap</label>
              <input
                className="form-input"
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="Budi Santoso"
                required
              />
            </div>

            {/* Email */}
            <div>
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="budi@developer.co.id"
                required
                autoComplete="email"
              />
            </div>

            {/* Phone */}
            <div>
              <label className="form-label">WhatsApp <span style={{ color: "var(--color-ink-3)", fontWeight: 400 }}>(opsional)</span></label>
              <input
                className="form-input"
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+62 812 xxxx xxxx"
              />
            </div>

            {/* Password */}
            <div>
              <label className="form-label">Kata Sandi</label>
              <div style={{ position: "relative" }}>
                <input
                  className="form-input"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Minimal 8 karakter"
                  required
                  minLength={8}
                  style={{ paddingRight: 40 }}
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--color-ink-3)" }}>
                  {showPassword ? <EyeOff size={15}/> : <Eye size={15}/>}
                </button>
              </div>
              {/* Password strength */}
              {passwordStrength && (
                <div style={{ marginTop: 6 }}>
                  <div style={{ height: 3, backgroundColor: "var(--color-paper-2)", borderRadius: 999, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: passwordStrength.width, backgroundColor: passwordStrength.color, borderRadius: 999, transition: "all 0.3s" }}/>
                  </div>
                  <div style={{ fontSize: 11, color: passwordStrength.color, marginTop: 3, fontWeight: 500 }}>
                    {passwordStrength.label}
                  </div>
                </div>
              )}
            </div>

            {/* Confirm password */}
            <div>
              <label className="form-label">Konfirmasi Kata Sandi</label>
              <div style={{ position: "relative" }}>
                <input
                  className="form-input"
                  type={showPassword2 ? "text" : "password"}
                  name="password2"
                  value={formData.password2}
                  onChange={handleChange}
                  placeholder="Ulangi kata sandi"
                  required
                  style={{ paddingRight: 40, borderColor: formData.password2 ? (passwordsMatch ? "var(--color-success)" : "var(--color-danger)") : undefined }}
                />
                <button type="button" onClick={() => setShowPassword2(!showPassword2)}
                  style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "var(--color-ink-3)" }}>
                  {showPassword2 ? <EyeOff size={15}/> : <Eye size={15}/>}
                </button>
              </div>
              {formData.password2 && (
                <div style={{ fontSize: 11, marginTop: 3, color: passwordsMatch ? "var(--color-success)" : "var(--color-danger)", fontWeight: 500 }}>
                  {passwordsMatch ? "✓ Kata sandi cocok" : "✗ Kata sandi tidak cocok"}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-accent"
              style={{ justifyContent: "center", width: "100%", marginTop: 4, opacity: isLoading ? 0.7 : 1 }}
            >
              {isLoading ? (
                <>
                  <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }}/>
                  Membuat akun...
                </>
              ) : (
                "Buat Akun →"
              )}
            </button>
          </form>

          <div style={{ marginTop: 20, textAlign: "center", fontSize: 12, color: "var(--color-ink-3)" }}>
            Sudah punya akun?{" "}
            <Link href="/login" style={{ color: "var(--color-accent)", fontWeight: 500, textDecoration: "none" }}>
              Masuk di sini
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
