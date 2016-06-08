from pyhermes import publisher


@publisher(topic='ralph2_sync_ack', auto_publish_result=True)
def publish_sync_ack_to_ralph3(obj, ralph3_id):
    """
    Publish ACK to Ralph3 that some object was updated.
    """
    return {
        'model': obj._meta.object_name,
        'id': obj.id,
        'ralph3_id': ralph3_id,
    }
