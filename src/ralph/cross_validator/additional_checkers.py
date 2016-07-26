

def ralph2_dhcp_checker(
    ralph2_objects, ralph3_objects, ralph3_model, missing_object_callback
):
    valid = invalid = 0
    for obj in ralph2_objects.all():
        try:
            ralph3_objects.get(ethernet__mac=obj.mac, address=obj.ip)
        except ralph3_model.DoesNotExist:
            missing_object_callback(obj)
            invalid += 1
        else:
            valid += 1
    return valid, invalid
