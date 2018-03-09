import falcon


def ensure_modifiable(model, props, exceptions=None, allow_immutables=False):
    """ Ensure the given properties of the given model are modifiable

    The model is expected to support two methods:
      protected_properties() returning a list which are never modifiable
      immutable_properties() returning a list which are write-once

    :param model: the class under scrutiny
    :param props: properties to consider
    :param exceptions: optional list of individual white-listed properties to
        allow
    :param allow_immutables: whether or not immutable properties are
        modifiable in this context or not. Defaults to False.
    :return: the list of exceptions + immutables which were found and allowed
    """
    if not exceptions:
        exceptions = []

    blacklist = model.protected_properties()
    if not allow_immutables:
        blacklist += model.immutable_properties()

    # ensure no immutable props included in props, should contain 'id'
    protected_props = [p.key for p in blacklist if p.key not in exceptions]
    intersecting = set(props.keys()) & set(protected_props)
    if intersecting:
        raise falcon.HTTPInvalidParam(msg="One or more properties are not "
                                          "modifiable.",
                                      param_name=repr(intersecting))
    return intersecting


def require_param(named, data_dict):
    """ Require that the given data dictionary contains the property named

    Will raise an appropriate falcon.HTTPBadRequest exception if not found

    :param named: the name of the key required to exist
    :param data_dict: the dictionay to inspect
    :return: the value of the required property, if found
    """
    try:
        result = data_dict[named]
    except KeyError:
        raise falcon.HTTPMissingParam(param_name=named)

    if not result:
        raise falcon.HTTPInvalidParam(msg=result,
                                      param_name=named)
    return result


def require_record(session, accessor, named, data_dict):
    """ Require that a persistent object exists in the DB

    Will raise an appropriate falcon.HTPBadRequest exception if not found

    :param session: the sqlalchemy session to use
    :param accessor: the data accessor object, usually class extending Base
    :param named: the property which contains the record primary key
    :param data_dict: the dictionary to look for the named property
    :return: the persistent object
    """
    record_id = require_param(named, data_dict)

    record = accessor.get(record_id, session)
    if not record:
        raise falcon.HTTPInvalidParam(msg=record_id,
                                      param_name=named)

    return record


def ensure_integer(named, value, minimum=None, maximum=None):
    if value == int(value):
        if not minimum or value >= minimum:
            if not maximum or value <= maximum:
                return

    raise falcon.HTTPInvalidParam(msg=value,
                                  param_name=named)
