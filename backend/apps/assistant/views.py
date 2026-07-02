# =============================================================================
# === backend/apps/assistant/views.py ===
# Sprint 15: Business Assistant — conversational AI for project intelligence.
#
# Architecture:
# - LLM as PRESENTER, never data source. All data from existing models.
# - classify_question() routes question → fetches only relevant data.
# - Tenant isolation: Project.objects.for_user() before ANY LLM call.
# - Suggested actions from Decision Engine — never LLM-generated.
# - LLM failure is handled gracefully — app stays functional without it.
# =============================================================================
import json
import logging

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project

logger = logging.getLogger(__name__)

# =============================================================================
# System prompt — Bahasa Indonesia, scoped to DevelopIndo context.
# Explicitly forbids hallucination: "JANGAN membuat asumsi"
# =============================================================================
SYSTEM_PROMPT = """
Kamu adalah Business Assistant untuk DevelopIndo, platform PropTech untuk developer properti Indonesia.
Tugasmu adalah membantu developer properti memahami status proyek mereka dan mengambil tindakan tepat.

Panduan menjawab:
- Gunakan Bahasa Indonesia yang profesional namun mudah dipahami
- Jawaban HARUS berdasarkan DATA yang diberikan saja — JANGAN membuat asumsi atau informasi di luar data
- Format: 2-4 kalimat utama, diikuti bullet points jika ada beberapa poin penting
- Maksimal 250 kata
- Jika ada blocker, sebutkan NAMA SPESIFIK requirement yang bermasalah
- Jika ada rekomendasi, sebutkan estimasi waktu dan dampak pada kesiapan
- Akhiri dengan satu kalimat actionable yang realistis
- Jangan ulangi data mentah — interpretasikan dan jelaskan dalam konteks bisnis properti
""".strip()

# =============================================================================
# Question router — maps keywords to data sources.
# "intelligence" is ALWAYS fetched (base context).
# Additional sources fetched only when the question warrants it.
# =============================================================================
def classify_question(question: str) -> list:
    q = question.lower()
    sources = ["intelligence"]  # always included

    risk_keywords     = ["risiko", "risk", "bahaya", "forecast", "proyeksi", "prediksi", "naik"]
    activity_keywords = ["aktivitas", "history", "riwayat", "log", "siapa", "kapan", "terakhir"]
    decision_keywords = ["harus", "selanjutnya", "tindakan", "langkah", "mulai", "blokir",
                         "mengapa", "kenapa", "why", "lakukan", "prioritas", "keputusan"]

    if any(kw in q for kw in risk_keywords):
        sources.append("risk_forecast")
    if any(kw in q for kw in activity_keywords):
        sources.append("activity")
    if any(kw in q for kw in decision_keywords):
        sources.append("decision")

    # Always include decision for general questions — most useful default
    if "decision" not in sources:
        sources.append("decision")

    return sources


class AssistantQueryView(APIView):
    """
    POST /api/assistant/query/

    Request body:
      {
        "project_id": "uuid",
        "question":   "Mengapa Cluster A diblokir?"
      }

    Response:
      {
        "success":           true,
        "project_id":        "uuid",
        "project_name":      "Perumahan Asri Cluster A",
        "question":          "Mengapa Cluster A diblokir?",
        "answer":            "Cluster A diblokir karena...",
        "suggested_actions": [
          {
            "rank":                 1,
            "label":                "Selesaikan Kontraktor",
            "action_type":          "primary",
            "status_id":            "uuid",
            "est_minutes":          17,
            "readiness_impact_pct": 60
          }
        ],
        "data_sources": ["intelligence", "decision"]
      }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data.get("project_id", "").strip()
        question   = request.data.get("question",   "").strip()

        # ── Input validation ──────────────────────────────────
        if not project_id:
            raise ValidationError({"project_id": "project_id wajib diisi."})
        if not question:
            raise ValidationError({"question": "Pertanyaan tidak boleh kosong."})
        if len(question) > 500:
            raise ValidationError({"question": "Pertanyaan terlalu panjang (maksimal 500 karakter)."})

        # ── Tenant isolation — FIRST, before any data fetch ───
        try:
            project = Project.objects.for_user(request.user).get(id=project_id)
        except (Project.DoesNotExist, Exception):
            raise NotFound("Proyek tidak ditemukan atau Anda tidak memiliki akses.")

        # ── Route → collect relevant data ─────────────────────
        sources = classify_question(question)
        context = self._build_context(project, sources)

        # ── Call Anthropic API (LLM as presenter only) ────────
        try:
            answer = self._call_llm(question, context)
        except Exception as e:
            logger.error(f"Business Assistant LLM error for project {project.id}: {e}")
            answer = (
                "Maaf, asisten sementara tidak tersedia. "
                "Silakan cek dashboard secara langsung untuk informasi terkini proyek Anda."
            )

        # ── Suggested actions — from Decision Engine, NEVER LLM ──
        suggested_actions = self._get_suggested_actions(project)

        return Response({
            "success":           True,
            "project_id":        str(project.id),
            "project_name":      project.name,
            "question":          question,
            "answer":            answer,
            "suggested_actions": suggested_actions,
            "data_sources":      sources,
        })

    def _build_context(self, project: Project, sources: list) -> dict:
        """
        Build structured data context from existing intelligence methods.
        The LLM only ever sees this dict — never raw DB queries.
        """
        intel = project.get_intelligence_summary()

        context = {
            "nama_proyek":          project.name,
            "lokasi":               project.location,
            "tahap_saat_ini":       project.stage_display,
            "kesiapan":             f"{intel['readiness_score']}%",
            "item_blokir":          intel["blocking_count"],
            "tingkat_risiko":       intel["risk_level_display"],
            "skor_risiko":          f"{intel['risk_score']}/100",
            "tindakan_berikutnya":  intel["next_action"] or "Tidak ada, semua requirement wajib selesai",
            "alerts_aktif":         [
                {"level": a["level"], "pesan": a["message"]}
                for a in (intel.get("alerts") or [])
            ],
            "requirements": [
                {
                    "nama":              r["name"],
                    "status":            r["status_display"],
                    "wajib":             r["is_mandatory"],
                    "terkunci_oleh":     r.get("unmet_prerequisites", []),
                    "memblokir_lainnya": r.get("prerequisites", []),
                    "jumlah_bukti":      r["evidence_count"],
                }
                for r in intel["requirements"]
            ],
        }

        if "decision" in sources:
            decision = project.get_decision_engine()
            if decision.get("has_recommendations") and decision.get("primary"):
                p = decision["primary"]
                context["rekomendasi_utama"] = {
                    "aksi":              p["action"],
                    "prioritas":         p["priority"],
                    "dampak_kesiapan":   f"+{p['readiness_impact_pct']}%",
                    "estimasi_waktu":    f"~{p['est_minutes']} menit",
                    "alasan":            p["reasons"],
                    "proyeksi_kesiapan": f"{decision['current_readiness']}% → {decision['projected_readiness']}%",
                }
            else:
                context["rekomendasi_utama"] = "Semua requirement wajib sudah selesai."

        if "risk_forecast" in sources:
            current  = project._get_risk_data()
            forecast = project._get_forecast_risk_data(days=14)
            context["proyeksi_risiko_14_hari"] = {
                "skor_saat_ini":  current["score"],
                "skor_proyeksi":  forecast["score"],
                "perubahan":      forecast["score"] - current["score"],
                "faktor_aktif":   [f["name"] for f in current["factors"]],
            }

        if "activity" in sources:
            recent = project.activity_timeline(limit=5)
            context["aktivitas_terbaru"] = [
                {"aksi": a["message"], "waktu": a["timestamp"][:10]}
                for a in recent
            ]

        return context

    def _call_llm(self, question: str, context: dict) -> str:
        """
        Call Anthropic API.
        Imported inside method so the app works even if anthropic
        package is not installed (graceful degradation).
        """
        from django.conf import settings
        import anthropic

        client  = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model      = "claude-sonnet-4-6",
            max_tokens = 500,
            system     = SYSTEM_PROMPT,
            messages   = [
                {
                    "role":    "user",
                    "content": (
                        f"Data proyek saat ini:\n"
                        f"{json.dumps(context, ensure_ascii=False, indent=2)}\n\n"
                        f"Pertanyaan dari developer: {question}"
                    ),
                }
            ],
        )
        return message.content[0].text

    def _get_suggested_actions(self, project: Project) -> list:
        """
        Suggested actions from Decision Engine only — NEVER from LLM.
        Keeps all recommendations grounded in real, auditable data.
        """
        try:
            decision = project.get_decision_engine()
            if not decision.get("has_recommendations") or not decision.get("primary"):
                return []

            p       = decision["primary"]
            actions = [{
                "rank":                 1,
                "label":                p["action"],
                "action_type":          "primary",
                "status_id":            p["status_id"],
                "est_minutes":          p["est_minutes"],
                "readiness_impact_pct": p["readiness_impact_pct"],
            }]
            for alt in decision.get("alternatives", [])[:2]:
                actions.append({
                    "rank":                 alt["rank"],
                    "label":                alt["action"],
                    "action_type":          "alternative",
                    "status_id":            alt.get("status_id"),
                    "est_minutes":          alt["est_minutes"],
                    "readiness_impact_pct": alt["readiness_impact_pct"],
                })
            return actions
        except Exception:
            return []
