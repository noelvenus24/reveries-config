
import pyblish.api
from maya import cmds

from reveries import lib
from reveries.plugins import RepairInstanceAction
from reveries.maya.plugins import MayaSelectInvalidInstanceAction


class SelectInvalid(MayaSelectInvalidInstanceAction):

    label = "Select Unfreezed"


class FreezeTransform(RepairInstanceAction):

    label = "Freeze Transform"


class ValidateTranformFreezed(pyblish.api.InstancePlugin):
    """ All `mesh` and `nurbsCurve` must be transform freezed

    Checking if translate, rotate, scale and shear freezed. When instance's
    family is `reveries.model`, will check all `transform` nodes.

    """

    order = pyblish.api.ValidatorOrder + 0.45
    hosts = ["maya"]
    label = "Transform Freezed"
    families = [
        "reveries.model",
    ]

    actions = [
        pyblish.api.Category("Select"),
        SelectInvalid,
        pyblish.api.Category("Fix It"),
        FreezeTransform,
    ]

    @classmethod
    def get_invalid(cls, instance):
        """Returns the invalid transforms in the instance.

        This is the same as checking:
        - translate == [0, 0, 0] and rotate == [0, 0, 0] and
          scale == [1, 1, 1] and shear == [0, 0, 0]

        Returns:
            list: Transforms that are not identity matrix

        """

        invalid = list()

        _identity = [1.0, 0.0, 0.0, 0.0,
                     0.0, 1.0, 0.0, 0.0,
                     0.0, 0.0, 1.0, 0.0,
                     0.0, 0.0, 0.0, 1.0]
        _tolerance = 1e-30

        for transform in cmds.ls(instance, type="transform", long=True):

            matrix = cmds.xform(transform,
                                query=True,
                                matrix=True,
                                objectSpace=True)

            if not lib.matrix_equals(_identity, matrix, _tolerance):
                invalid.append(transform)

        return invalid

    def process(self, instance):

        invalid = self.get_invalid(instance)
        if invalid:
            self.log.error(
                "{!r} has not freezed transform:".format(instance.name)
            )
            for node in invalid:
                self.log.error(node)

            raise ValueError("%s <Transform Freezed> Failed." % instance.name)

        self.log.info("%s <Transform Freezed> Passed." % instance.name)

    @classmethod
    def fix_invalid(cls, instance):
        """Freeze transforms"""
        for item in cls.get_invalid(instance):
            cmds.makeIdentity(item, apply=True)
