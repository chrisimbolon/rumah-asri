"use client";

import { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login, isLoading, error, clearError } = useAuth();

  const [formData, setFormData] = useState({
    email:    "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    clearError();
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(formData);
  }

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

        {/* Grid bg */}
        <div className="absolute inset-0 opacity-[0.04]"
          style={{ backgroundImage: "linear-gradient(white 1px,transparent 1px),linear-gradient(90deg,white 1px,transparent 1px)", backgroundSize: "48px 48px" }}
        />

        {/* Building SVG */}
        <div className="relative z-10 flex-1 flex items-center justify-center my-8">
          <svg viewBox="0 0 320 300" className="w-4/5">
            <rect x="40" y="120" width="240" height="178" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.12)" strokeWidth="1"/>
            <rect x="60" y="68"  width="200" height="66"  fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.08)" strokeWidth="1"/>
            <rect x="85" y="32"  width="150" height="44"  fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.06)" strokeWidth="1"/>
            <line x1="40" y1="120" x2="280" y2="120" stroke="#B8935A" strokeWidth="1" opacity="0.5"/>
            {[52,100,150,200,248].map((x, i) => (
              <rect key={i} x={x} y={140} width={34} height={48} fill="rgba(26,63,168,0.25)" stroke="rgba(26,63,168,0.35)" strokeWidth="0.5"/>
            ))}
            <rect x="133" y="202" width="54" height="96" fill="rgba(26,63,168,0.15)" stroke="rgba(255,255,255,0.12)" strokeWidth="0.5"/>
          </svg>
        </div>

        {/* Testimonial */}
        <div className="relative z-10">
          <blockquote style={{ fontFamily: "var(--font-serif)", fontSize: 17, fontStyle: "italic", color: "rgba(255,255,255,0.7)", lineHeight: 1.6, marginBottom: 12 }}>
            "Platform ini mengubah cara kami mengelola proyek. Pembeli lebih puas karena bisa lihat progres kapan saja."
          </blockquote>
          <div style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }}>
            — Rizky Setiawan, Agen Senior · Cluster A
          </div>
        </div>
      </div>

      {/* ── Right — form ── */}
      <div className="flex items-center justify-center p-8">
        <div className="w-full max-w-sm">

          {/* Mobile logo */}
          <div className="md:hidden mb-8" style={{ fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 600, color: "var(--color-ink)" }}>
            Rumah<span style={{ color: "var(--color-accent)" }}>Asri</span>
          </div>

          <h1 style={{ fontSize: 24, fontWeight: 600, color: "var(--color-ink)", marginBottom: 8 }}>
            Selamat datang kembali
          </h1>
          <p style={{ fontSize: 13, color: "var(--color-ink-3)", marginBottom: 28 }}>
            Masuk ke akun platform RumahAsri Anda
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
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <label className="form-label">Email</label>
              <input
                className="form-input"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="nama@email.co.id"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="form-label">Kata Sandi</label>
              <div style={{ position: "relative" }}>
                <input
                  className="form-input"
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  required
                  autoComplete="current-password"
                  style={{ paddingRight: 40 }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: "absolute", right: 12, top: "50%",
                    transform: "translateY(-50%)", background: "none",
                    border: "none", cursor: "pointer",
                    color: "var(--color-ink-3)",
                  }}
                >
                  {showPassword ? <EyeOff size={15}/> : <Eye size={15}/>}
                </button>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                <input type="checkbox" style={{ cursor: "pointer" }}/>
                <span style={{ fontSize: 12, color: "var(--color-ink-3)" }}>Ingat saya</span>
              </label>
              <a style={{ fontSize: 12, color: "var(--color-accent)", cursor: "pointer", textDecoration: "none" }}>
                Lupa kata sandi?
              </a>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-accent"
              style={{ justifyContent: "center", width: "100%", opacity: isLoading ? 0.7 : 1 }}
            >
              {isLoading ? (
                <>
                  <Loader2 size={15} style={{ animation: "spin 1s linear infinite" }}/>
                  Memverifikasi...
                </>
              ) : (
                "Masuk →"
              )}
            </button>
          </form>

          <div style={{ marginTop: 24, textAlign: "center", fontSize: 12, color: "var(--color-ink-3)" }}>
            Belum punya akun?{" "}
            <Link href="/register" style={{ color: "var(--color-accent)", fontWeight: 500, textDecoration: "none" }}>
              Daftar sekarang
            </Link>
          </div>

          {/* Demo hint */}
          <div style={{
            marginTop: 24, padding: "12px 14px",
            backgroundColor: "var(--color-accent-light)",
            borderRadius: 6, fontSize: 12, color: "var(--color-accent)",
          }}>
            <strong>Demo:</strong> admin@asrisentosa.co.id · RumahAsri2026!
          </div>
        </div>
      </div>
    </div>
  );
}
