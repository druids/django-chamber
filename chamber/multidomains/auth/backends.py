from __future__ import unicode_literals

from django.contrib.auth.backends import ModelBackend as OridginModelBackend
from django.contrib.auth.models import Permission

from chamber.multidomains.domain import get_user_class


class ModelBackend(OridginModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_class()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)

    def get_group_permissions(self, user_obj, obj=None):
        """
        Returns a set of permission strings that this user has through his/her
        groups.
        """
        if user_obj.is_anonymous() or obj is not None:
            return set()
        if not hasattr(user_obj, '_group_perm_cache'):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                user_groups_field = get_user_class()._meta.get_field('groups')
                user_groups_query = 'group__%s' % user_groups_field.related_query_name()
                perms = Permission.objects.filter(**{user_groups_query: user_obj})
            perms = perms.values_list('content_type__app_label', 'codename').order_by()
            user_obj._group_perm_cache = set(["%s.%s" % (ct, name) for ct, name in perms])
        return user_obj._group_perm_cache

    def get_user(self, user_id):
        UserModel = get_user_class()
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None