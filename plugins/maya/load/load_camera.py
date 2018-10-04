
import avalon.api
import reveries.maya.lib
from reveries.maya.plugins import ReferenceLoader


class CameraLoader(ReferenceLoader, avalon.api.Loader):
    """Specific loader for the reveries.camera family"""

    label = "Reference camera"
    order = -10
    icon = "code-fork"
    color = "orange"

    hosts = ["maya"]

    families = ["reveries.camera"]

    representations = [
        "mayaAscii",
        "Alembic",
        "FBX",
    ]

    def process_reference(self, context, name, namespace, options):
        import maya.cmds as cmds

        representation = context["representation"]

        entry_path = self.file_path(representation["data"]["entry_fname"])

        group_name = "{}:{}".format(namespace, name)
        nodes = cmds.file(entry_path,
                          namespace=namespace,
                          sharedReferenceFile=False,
                          groupReference=True,
                          groupName=group_name,
                          reference=True,
                          lockReference=True,
                          returnNewNodes=True)

        reveries.maya.lib.lock_transform(group_name)
        self[:] = nodes

        self.interface = cmds.listRelatives(cmds.ls(nodes, type="camera"),
                                            parent=True)

        return group_name

    def switch(self, container, representation):
        self.update(container, representation)
