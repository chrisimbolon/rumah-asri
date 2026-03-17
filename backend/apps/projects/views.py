"""
RumahAsri — Projects Views

Endpoints:
  GET  /api/projects/          ← list all projects for developer
  POST /api/projects/          ← create new project
  GET  /api/projects/<id>/     ← get single project
  PUT  /api/projects/<id>/     ← update project
  DEL  /api/projects/<id>/     ← delete project
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project
from .serializers import ProjectCreateSerializer, ProjectSerializer


class ProjectListView(APIView):
    """GET /api/projects/ — POST /api/projects/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Developer sees their own projects
        # Super admin sees all
        if request.user.role == "super_admin":
            projects = Project.objects.all()
        else:
            projects = Project.objects.filter(developer=request.user)

        serializer = ProjectSerializer(projects, many=True)
        return Response({
            "success": True,
            "count":   projects.count(),
            "results": serializer.data,
        })

    def post(self, request):
        # Only developers and super admins can create projects
        if request.user.role not in ["developer", "super_admin"]:
            return Response(
                {"success": False, "message": "Tidak memiliki izin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ProjectCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid():
            project = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": f"Proyek '{project.name}' berhasil dibuat",
                    "project": ProjectSerializer(project).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ProjectDetailView(APIView):
    """GET/PUT/DELETE /api/projects/<id>/"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            project = Project.objects.get(pk=pk)
            # Check ownership
            if user.role != "super_admin" and project.developer != user:
                return None, "Tidak memiliki izin untuk proyek ini"
            return project, None
        except Project.DoesNotExist:
            return None, "Proyek tidak ditemukan"

    def get(self, request, pk):
        project, error = self.get_object(pk, request.user)
        if error:
            return Response(
                {"success": False, "message": error},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProjectSerializer(project)
        return Response({"success": True, "project": serializer.data})

    def put(self, request, pk):
        project, error = self.get_object(pk, request.user)
        if error:
            return Response(
                {"success": False, "message": error},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProjectCreateSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Proyek berhasil diperbarui",
                "project": ProjectSerializer(project).data,
            })
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        project, error = self.get_object(pk, request.user)
        if error:
            return Response(
                {"success": False, "message": error},
                status=status.HTTP_404_NOT_FOUND,
            )
        name = project.name
        project.delete()
        return Response({
            "success": True,
            "message": f"Proyek '{name}' berhasil dihapus",
        })