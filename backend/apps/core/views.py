# =============================================================================
# === apps/core/views.py ===
# =============================================================================
"""
Shared tenant-scoping base view.

Every detail/list endpoint for a tenant-owned model should subclass this
instead of hand-rolling get_object()/get_queryset(). Set `model` on the
subclass. get_object() and get_queryset() cannot be written insecurely
from here — there is no unscoped `Model.objects.get()` call anywhere in
this class, only `Model.objects.for_user(...)`.
"""
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class TenantScopedAPIView(APIView):
    model = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.model is None:
            raise NotImplementedError(f"{self.__class__.__name__} must set `model`.")
        return self.model.objects.for_user(self.request.user)

    def get_object(self, pk):
        try:
            return self.get_queryset().get(pk=pk)
        except self.model.DoesNotExist:
            raise NotFound("Tidak ditemukan, atau Anda tidak memiliki akses.")
