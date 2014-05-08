import ckan.logic.auth as logic_auth
import ckan.new_authz as new_authz
from ckan.common import _


def package_delete(context, data_dict):
    user = context.get('user')
    package = logic_auth.get_package_object(context, data_dict)

    can_package_update = new_authz.is_authorized(
        'package_update', context, {'id': package.id})

    if can_package_update.get('success'):
        return can_package_update
    else:
        return {'success': False,
                'msg': _('User %s not authorized to delete package %s') %
                        (str(user), package.id)}
