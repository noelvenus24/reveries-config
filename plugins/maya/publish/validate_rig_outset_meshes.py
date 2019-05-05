
import pyblish.api

from maya import cmds

from reveries.plugins import depended_plugins_succeed
from reveries.maya.plugins import MayaSelectInvalidInstanceAction


class SelectInvalidOutNodes(MayaSelectInvalidInstanceAction):

    label = "Invalid Out Nodes"


class ValidateRigOutSetMeshes(pyblish.api.InstancePlugin):
    """Ensure rig OutSet member node type correct

    `OutSet` can only contain models

    """

    label = "Rig OutSet Meshes"
    order = pyblish.api.ValidatorOrder + 0.11
    hosts = ["maya"]

    families = ["reveries.rig"]

    actions = [
        pyblish.api.Category("Select"),
        SelectInvalidOutNodes,
    ]

    dependencies = [
        "ValidateRigContents",
    ]

    def process(self, instance):
        invalid = self.get_invalid(instance)
        if invalid:
            raise Exception(
                "'%s' has invalid out nodes:\n%s" % (
                    instance,
                    ",\n".join(
                        "'" + member + "'" for member in invalid))
            )

    @classmethod
    def get_geometries(cls, instance):
        geometries = set()

        for out_set in instance.data["outSets"]:
            nodes = cmds.sets(out_set, query=True)
            if not nodes:
                cls.log.warning("Rig instance's OutSet %s is empty" % out_set)
                continue

            geometries.update(nodes)

        return list(geometries)

    @classmethod
    def get_invalid(cls, instance):

        if not depended_plugins_succeed(cls, instance):
            raise Exception("Depended plugin failed. See error log.")

        invalid = list()

        for node in cls.get_geometries(instance):
            if not cmds.nodeType(node) == "transform":
                invalid.append(node)
                continue

            children = cmds.listRelatives(node,
                                          children=True,
                                          fullPath=True) or []

            if not children:
                invalid.append(node)
                continue

            for chd in children:
                if not cmds.ls(chd, type=("mesh", "constraint")):
                    invalid.append(node)
                    break

        return invalid
