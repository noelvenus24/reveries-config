
import pyblish.api
import maya.cmds as cmds

from reveries.maya import lib, pipeline


class CollectDeformedOutputs(pyblish.api.InstancePlugin):
    """從選取的物件中篩選可被 cache 的物件

    !!! 注意: 只有 visible 物件會被 cache

    篩選方法有兩個:

        1. 選取 Subset Group 節點 (紅色包裹圖示的物件)，然後該 Subset
           帶有 OutSet 或 名字以 OutSet 結尾的 objectSet，這時候只會
           從那個 objectSet 取得要被 cache 的物件。 這個方法主要是使用
           在輸出角色 cache的時候，通常只有 Rig 會有 OutSet。

        2. 如果找不到 OutSet (方法 1 失敗)，那就會篩選選取物件的整個階
           層，從中挑選可以被 cache 的物件。

    如果是使用 OutSet 的方式 (方法 1) 來引導系統的話，Subset 的名字也
    會受 OutSet 的前綴影響，例如:

             "OutSet" -> "pointcache.Boy_model_01_Default"
          "SimOutSet" -> "pointcache.Boy_model_01_Sim"
        "ClothOutSet" -> "pointcache.Boy_model_01_Cloth"

    """

    """Collect out geometry data for instance.

    Only visible objects will be cached.

    If the caching source has any objectSet which name is or endswith
    "OutSet", will create instances from them. For "OutSet" that has
    prefix, will use that prefix as variant of subset.

    For example:
             "OutSet" -> "pointcache.Boy_model_01_Default"
          "SimOutSet" -> "pointcache.Boy_model_01_Sim"
        "ClothOutSet" -> "pointcache.Boy_model_01_Cloth"

    If no "OutSet", collect deformable nodes directly from instance
    member (selection).

    """

    order = pyblish.api.CollectorOrder - 0.2999
    label = "篩選 pointcache 物件"
    hosts = ["maya"]
    families = [
        "reveries.pointcache",
    ]

    def process(self, instance):

        # Frame range
        if instance.data["staticCache"]:
            start_frame = cmds.currentTime(query=True)
            end_frame = cmds.currentTime(query=True)
        else:
            get = (lambda f: cmds.playbackOptions(query=True, **f))
            start_frame = get({"minTime": True})
            end_frame = get({"maxTime": True})

        members = instance[:]
        out_sets = list()

        # Find OutSet from *Subset Group nodes*
        #
        for group in cmds.ls(members, type="transform", long=True):
            if cmds.listRelatives(group, shapes=True):
                continue

            try:
                container = pipeline.get_container_from_group(group)
            except AssertionError:
                # Not a subset group node
                continue

            nodes = cmds.sets(container, query=True)
            sets = [
                s for s in cmds.ls(nodes, type="objectSet")
                if s.endswith("OutSet")
            ]
            if sets:
                out_sets += sets
                members.remove(group)

        # Collect cacheable nodes

        created = False
        backup = instance

        if out_sets:
            # Cacheables from OutSet of loaded subset
            out_cache = dict()
            subset = instance.data["subset"][len("pointcache"):]

            for out_set in out_sets:

                variant = out_set.rsplit(":", 1)[-1][:-len("OutSet")]
                if variant:
                    name = variant + "." + subset
                else:
                    name = subset

                self.log.info(name)

                namespace = lib.get_ns(out_set)
                set_member = cmds.ls(cmds.sets(out_set, query=True), long=True)
                cacheables = lib.pick_cacheable(set_member)
                cacheables = lib.get_visible_in_frame_range(cacheables,
                                                            int(start_frame),
                                                            int(end_frame))
                # Plus locator
                cacheables += self.pick_locators(set_member)

                out_cache[(namespace, name)] = cacheables

                for n in cacheables:
                    if n in members:
                        members.remove(n)

            # Re-Create instances
            context = instance.context
            source_data = instance.data

            for (namespace, name), cacheables in out_cache.items():

                if not cacheables:
                    self.log.debug("Skip empty OutSet %s in %s"
                                   % (name, namespace))
                    continue

                namespace = namespace[1:]  # Remove root ":"
                # For filesystem, remove other ":" if the namespace is nested
                namespace = namespace.replace(":", "._.")

                instance = context.create_instance(namespace + "." + name)
                created = True

                instance.data.update(source_data)

                # New subset name
                #
                instance.data["subset"] = ".".join(["pointcache",
                                                    namespace,
                                                    name])
                instance[:] = cacheables
                instance.data["outCache"] = cacheables
                instance.data["requireAvalonUUID"] = cacheables
                instance.data["startFrame"] = start_frame
                instance.data["endFrame"] = end_frame

        if not members:
            # Nothing left, all in/has OutSet

            if not created:
                cmds.error("No pointcache instance created.")
            else:
                context.remove(backup)

        else:
            # Cache nodes that were not in any OutSet

            instance = backup

            # Cacheables from instance member
            cacheables = lib.pick_cacheable(members)
            cacheables = lib.get_visible_in_frame_range(cacheables,
                                                        int(start_frame),
                                                        int(end_frame))
            # Plus locator
            cacheables += self.pick_locators(members)

            instance[:] = cacheables
            instance.data["outCache"] = cacheables
            instance.data["requireAvalonUUID"] = cacheables
            instance.data["startFrame"] = start_frame
            instance.data["endFrame"] = end_frame

    def pick_locators(self, members):
        return cmds.listRelatives(cmds.ls(members, type="locator"),
                                  parent=True,
                                  fullPath=True) or []
