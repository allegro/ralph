import re
from ralph.business.models import Venture, VentureRole

def slug_validation(data):
    if re.match(r'^[a-z]{1}[a-z0-9_]*[a-z0-9]{1}$', data):
        return False
    return True


def invalid_ventures():
    ventures = Venture.objects.all()
    list = []
    for venture in ventures:
        if not re.match(r'^[a-z]{1}[a-z0-9_]*[a-z0-9]{1}$', venture.symbol):
            list.append({'venture': venture.name, 'venture_id': venture.id, 'symbol': venture.symbol})
    return list

def invalid_roles():
    roles = VentureRole.objects.all()
    list = []
    for role in roles:
        if not re.match(r'^[a-z]{1}[a-z0-9_]*[a-z0-9]{1}$', role.name):
            list.append({'role': role.name, 'role_id': role.id})
    return list
