from django.db import models
from model_utils.models import TimeStampedModel

from authentication.models import UserStampedModel
from core.utils import get_upload_path


class File(TimeStampedModel, UserStampedModel):
    file = models.FileField(upload_to=get_upload_path)
