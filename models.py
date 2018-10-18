from django.db import models

class Emblem(models.Model):
    item_hash = models.BigIntegerField(primary_key=True)
    #index = models.IntegerField(null=True)
    collectible_hash = models.BigIntegerField(null=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    tier = models.CharField(max_length=20)
    icon = models.URLField(max_length=200)
    secondary_icon = models.URLField(max_length=200)
    main_objective = models.ForeignKey('Objective', on_delete=models.SET_NULL, null=True)
    main_emblem = models.ForeignKey('self', on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return self.name
    @property
    def sub_objectives(self):
        return [obj for obj in self.objective_set.all() if obj.pk != self.main_objective.pk]

class Objective(models.Model):
    item_hash = models.BigIntegerField(primary_key=True)
    main_emblem = models.ForeignKey('Emblem', on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    progress_description = models.TextField()
    def __str__(self):
        return self.description if len(self.description) > 0 else self.progress_description

class Player(models.Model):
    membership_type = models.IntegerField()
    membership_id = models.BigIntegerField()
    player_data = models.TextField(null=True)
    class Meta:
        unique_together = (("membership_type", "membership_id"),)