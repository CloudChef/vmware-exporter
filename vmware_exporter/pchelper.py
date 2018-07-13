import pyVmomi


def create_filter_spec(view_ref, obj_type, path_set, vm=None):
    if obj_type is pyVmomi.vim.VirtualMachine:
        obj_spec = pyVmomi.vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = vm
    else:
        obj_spec = pyVmomi.vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True

        traversal_spec = pyVmomi.vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]

    property_spec = pyVmomi.vmodl.query.PropertyCollector.PropertySpec(
        all=False)
    property_spec.type = obj_type

    if not path_set:
        property_spec.all = True

    property_spec.pathSet = path_set

    return(obj_spec, property_spec)


def collect_properties(service_instance, view_ref, obj_type, path_set=None,
                       include_mors=False, vms={}):
    """
    Collect properties for managed objects from a view ref
    Check the vSphere API documentation for example on retrieving
    object properties:
        - http://goo.gl/erbFDz
    Args:
        si          (ServiceInstance): ServiceInstance connection
        view_ref (pyVmomi.vim.view.*): Starting point of inventory navigation
        obj_type      (pyVmomi.vim.*): Type of managed object
        path_set               (list): List of properties to retrieve
        include_mors           (bool): If True include the managed objects
                                       refs in the result
    Returns:
        A list of properties for the managed objects
    """
    collector = service_instance.content.propertyCollector

    # Create object specification to define the starting point of
    # inventory navigation
    obj_specs = []
    property_specs = []

    if obj_type is pyVmomi.vim.VirtualMachine:
        for vm in view_ref.view:
            if vm._moId not in vms:
                continue
            (obj_spec, property_spec) = create_filter_spec(
                view_ref, obj_type, path_set, vm)
            obj_specs.append(obj_spec)
            property_specs.append(property_spec)
    else:
        (obj_spec, property_spec) = create_filter_spec(
            view_ref, obj_type, path_set)
        obj_specs.append(obj_spec)
        property_specs.append(property_spec)

    if not obj_specs:
        return []

    # Add the object and property specification to the
    # property filter specification
    filter_spec = pyVmomi.vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = property_specs

    # Retrieve properties
    options = pyVmomi.vmodl.query.PropertyCollector.RetrieveOptions()
    props = collector.RetrievePropertiesEx([filter_spec], options)
    objects = props.objects
    token = props.token
    while token:
        continue_props = collector.ContinueRetrievePropertiesEx(token)
        objects.extend(continue_props.objects)
        token = continue_props.token
    data = []
    for obj in objects:
        properties = {}
        for prop in obj.propSet:
            properties[prop.name] = prop.val

        if include_mors:
            properties['obj'] = obj.obj

        data.append(properties)
    return data
