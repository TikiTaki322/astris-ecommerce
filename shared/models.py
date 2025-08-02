from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def __init__(self, alive_only=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alive_only = alive_only

    def get_queryset(self):
        qs = super().get_queryset()
        if self.alive_only:
            return qs.filter(deleted_at__isnull=True)
        return qs


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    objects = SoftDeleteManager()  # Alive
    all_objects = SoftDeleteManager(alive_only=False)  # All

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)
