
import pyblish.api


class ValidatePrimitiveHierarchyPaths(pyblish.api.InstancePlugin):
    """Validate all primitives build hierarchy from attribute when enabled.

    The name of the attribute must exist on the prims and have the same name
    as Build Hierarchy from Attribute's `Path Attribute` value on the Alembic
    ROP node whenever Build Hierarchy from Attribute is enabled.

    """

    order = pyblish.api.ValidatorOrder + 0.1
    label = "Validate Prims Hierarchy Path"
    hosts = ["houdini"]
    families = [
        "reveries.pointcache",
    ]

    def process(self, instance):
        invalid = self.get_invalid(instance)
        if invalid:
            raise RuntimeError("See log for details. "
                               "Invalid nodes: {0}".format(invalid))

    @classmethod
    def get_invalid(cls, instance):

        output = instance.data["output_node"]

        rop = instance[0]
        build_from_path = rop.parm("build_from_path").eval()
        if not build_from_path:
            cls.log.debug("Alembic ROP has 'Build from Path' disabled. "
                          "Validation is ignored..")
            return

        path_attr = rop.parm("path_attrib").eval()
        if not path_attr:
            cls.log.error("The Alembic ROP node has no Path Attribute"
                          "value set, but 'Build Hierarchy from Attribute'"
                          "is enabled.")
            return [rop.path()]

        cls.log.debug("Checking for attribute: %s" % path_attr)

        # Check if the primitive attribute exists
        geo = output.geometry()
        attrib = geo.findPrimAttrib("path")
        if not attrib:
            cls.log.info("Geometry Primitives are missing "
                         "path attribute: `%s`" % path_attr)
            return [output.path()]

        # Ensure at least a single string value is present
        if not attrib.strings():
            cls.log.info("Primitive path attribute has no "
                         "string values: %s" % path_attr)
            return [output.path()]

        # Ensure all primitives are set to a valid path
        # Collect all invalid primitive numbers
        invalid_prims = []
        paths = geo.primStringAttribValues(path_attr)
        for i, path in enumerate(paths):
            if not path:
                # Empty path value is invalid.
                invalid_prims.append(i)
                continue

        if invalid_prims:
            num_prims = len(geo.iterPrims())  # faster than len(geo.prims())
            cls.log.info("Prims have no value for attribute `%s` "
                         "(%s of %s prims)" % (path_attr,
                                               len(invalid_prims),
                                               num_prims))
            return [output.path()]
