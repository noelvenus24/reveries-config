
import pyblish.api
import avalon.io
from maya import cmds


class CollectLook(pyblish.api.InstancePlugin):
    """Collect mesh's shading network and objectSets
    """

    order = pyblish.api.CollectorOrder + 0.2
    hosts = ["maya"]
    label = "Collect Look"
    families = ["reveries.look"]

    def process(self, instance):
        meshes = cmds.ls(instance,
                         visible=True,
                         noIntermediate=True,
                         type="mesh")

        # Collect shading networks
        shaders = cmds.listConnections(meshes, type="shadingEngine")
        upstream_nodes = cmds.listHistory(shaders, pruneDagObjects=True)

        instance.data["look_members"] = upstream_nodes
        instance[:] += upstream_nodes

        # Collect previous texture file hash.
        # dict {hash: "/file/path"}
        instance.data["look_textures"] = dict()

        subset = instance.data["subset_doc"]
        if subset is None:
            return

        version = avalon.io.find_one({"type": "version",
                                      "parent": subset["_id"]},
                                     {"name": True},
                                     sort=[("name", -1)])
        if version is None:
            return

        representation = avalon.io.find_one({"type": "representation",
                                             "name": "LookDev",
                                             "parent": version["_id"]},
                                            {"data.textures": True})
        if representation is None:
            raise Exception("Version exists but no representation, "
                            "this is a bug.")

        instance.data["look_textures"] = representation["data"]["textures"]
