from django.conf import settings
from django.db import models


class GamerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gamer_profile")
    nickname = models.CharField(max_length=40, unique=True)
    favorite_genre = models.CharField(max_length=60, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return self.nickname


class Game(models.Model):
    title = models.CharField(max_length=120)
    genre = models.CharField(max_length=60)
    platform = models.CharField(max_length=60)
    launch_year = models.PositiveIntegerField()
    synopsis = models.TextField()
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)
    technical_sheet = models.FileField(upload_to="technical_sheets/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class LibraryEntry(models.Model):
    STATUS_CHOICES = [("pendiente", "Pendiente"), ("jugando", "Jugando"), ("completado", "Completado")]
    gamer = models.ForeignKey(GamerProfile, on_delete=models.CASCADE, related_name="library_entries")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="library_entries")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pendiente")
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        constraints = [models.UniqueConstraint(fields=["gamer", "game"], name="unique_game_per_gamer")]

    def __str__(self):
        return f"{self.gamer} - {self.game}"
