from django.http import HttpRequest
from django.contrib.auth import get_user_model
from ninja import Router
from ninja.security import django_auth
import user.schema as schema

User = get_user_model()

router = Router()

@router.get("/current-user", response=schema.User, tags=["account"], auth=django_auth)
def current_user(request: HttpRequest):
    return User.objects.get(pk=request.user.id)