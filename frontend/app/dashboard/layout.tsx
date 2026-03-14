import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        backgroundColor: "var(--color-paper)",
        overflow: "hidden",
      }}
    >
      {/* ── Left — Sidebar ── */}
      <Sidebar />

      {/* ── Right — Main content area ── */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
          overflow: "hidden",
        }}
      >
        {/* Sticky topbar */}
        <Topbar />

        {/* Scrollable page content */}
        <main
          style={{
            flex: 1,
            overflowY: "auto",
            padding: 24,
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
