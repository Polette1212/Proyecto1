from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import GameForm, GamerProfileForm, LibraryEntryForm
from .models import Game, GamerProfile, LibraryEntry

MODULES = {
    "games": {"model": Game, "form": GameForm, "title": "Videojuegos", "icon": "🕹️", "fields": ["title", "genre", "platform", "launch_year"]},
    "gamers": {"model": GamerProfile, "form": GamerProfileForm, "title": "Perfiles gamer", "icon": "👾", "fields": ["nickname", "user", "favorite_genre"]},
    "library": {"model": LibraryEntry, "form": LibraryEntryForm, "title": "Biblioteca", "icon": "⚡", "fields": ["gamer", "game", "status", "score"]},
}

def role_for(user):
    if user.is_superuser or user.groups.filter(name="Administrador").exists(): return "Administrador"
    if user.groups.filter(name="Operador").exists(): return "Operador"
    return "Consulta"

def can_write(user): return role_for(user) in {"Administrador", "Operador"}

@login_required
def dashboard(request):
    return render(request, "vault/dashboard.html", {"game_count": Game.objects.count(), "gamer_count": GamerProfile.objects.count(), "entry_count": LibraryEntry.objects.count(), "recent_entries": LibraryEntry.objects.select_related("gamer", "game")[:5], "role": role_for(request.user)})

@login_required
def record_list(request, module):
    config = MODULES.get(module)
    if not config: return redirect("vault_dashboard")
    query = request.GET.get("q", "").strip(); objects = config["model"].objects.all()
    if query:
        filters = Q(title__icontains=query) | Q(genre__icontains=query) | Q(platform__icontains=query) if module == "games" else Q(nickname__icontains=query) | Q(user__username__icontains=query) if module == "gamers" else Q(gamer__nickname__icontains=query) | Q(game__title__icontains=query) | Q(status__icontains=query)
        objects = objects.filter(filters)
    return render(request, "vault/list.html", {"config": config, "module": module, "objects": objects, "query": query, "role": role_for(request.user), "can_write": can_write(request.user)})

@login_required
def record_form(request, module, pk=None):
    config = MODULES.get(module)
    if not config or not can_write(request.user):
        messages.error(request, "Tu perfil solo puede consultar información."); return redirect("vault_list", module=module if config else "games")
    instance = get_object_or_404(config["model"], pk=pk) if pk else None
    form = config["form"](request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Registro guardado correctamente."); return redirect("vault_list", module=module)
    return render(request, "vault/form.html", {"form": form, "config": config, "module": module, "record": instance})

@login_required
def record_delete(request, module, pk):
    config = MODULES.get(module)
    if not config or role_for(request.user) != "Administrador":
        messages.error(request, "Solo el perfil Administrador puede eliminar registros."); return redirect("vault_list", module=module if config else "games")
    record = get_object_or_404(config["model"], pk=pk)
    if request.method == "POST":
        record.delete(); messages.success(request, "Registro eliminado."); return redirect("vault_list", module=module)
    return render(request, "vault/confirm_delete.html", {"config": config, "module": module, "record": record})