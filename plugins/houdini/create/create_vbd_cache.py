from avalon import houdini


class CreateVDBCache(houdini.Creator):
    """OpenVDB from Geometry ROP"""

    label = "VDB Cache"
    family = "reveries.vdbcache"
    icon = "qrcode"

    def __init__(self, *args, **kwargs):
        super(CreateVDBCache, self).__init__(*args, **kwargs)

        # Remove the `active`, we are checking the `bypass` flag of the nodes
        self.data.pop("active", None)

        # Set node type to create for output
        self.data["node_type"] = "geometry"

    def process(self):
        instance = super(CreateVDBCache, self).process()

        file_path = "$HIP/pyblish/%s/%s.$F4.vdb" % (self.name, self.name)

        parms = {"sopoutput": file_path,
                 "initsim": True}

        if self.nodes:
            node = self.nodes[0]
            parms.update({"soppath": node.path()})

        instance.setParms(parms)
