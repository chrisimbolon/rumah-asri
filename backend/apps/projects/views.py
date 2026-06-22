# =============================================================================
# === apps/projects/views.py ===
# =============================================================================
"""
DevelopIndo — Projects Views
All access control now flows through TenantScopedAPIView / Project.objects.for_user()
"""
from rest_framework import status
from rest_framework.response import Response

from apps.core.views import TenantScopedAPIView

from .models import Project
from .serializers import ProjectCreateSerializer, ProjectSerializer


class ProjectListView(TenantScopedAPIView):
    model = Project

    def get(self, request):
        projects = self.get_queryset()
        serializer = ProjectSerializer(projects, many=True)
        return Response({
            "success": True,
            "count":   projects.count(),
            "results": serializer.data,
        })

    def post(self, request):
        if request.user.role not in ("developer", "super_admin"):
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ProjectCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            project = serializer.save()
            return Response({
                "success": True,
                "message": f"Proyek '{project.name}' berhasil dibuat",
                "project": ProjectSerializer(project).data,
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProjectDetailView(TenantScopedAPIView):
    model = Project

    def get(self, request, pk):
        project = self.get_object(pk)
        return Response({"success": True, "project": ProjectSerializer(project).data})

    def put(self, request, pk):
        project = self.get_object(pk)
        serializer = ProjectCreateSerializer(
            project, data=request.data, partial=True, context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Proyek berhasil diperbarui",
                "project": ProjectSerializer(project).data,
            })
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        project = self.get_object(pk)
        name = project.name
        project.delete()
        return Response({"success": True, "message": f"Proyek '{name}' berhasil dihapus"})

