import ckan.model as model
import ckan.logic.auth as logic_auth
from ckan.common import _


def package_update(context, data_dict):
    '''Only allow creator of a package to update it '''
    user = context.get('user')
    user_obj = model.User.get(user)
    package = logic_auth.get_package_object(context, data_dict)

    if package.creator_user_id == user_obj.id:
        return {'success': True }
    else:
        return {'success': False,
                'msg': _('User %s not authorized to edit package %s') %
                        (str(user), package.id)}
