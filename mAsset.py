import uuid
import json
import logging
import datetime
from pprint import pformat
import pymel.core as pCore
import maya.OpenMaya as om

import metaData
import __main__

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

ASSET_TYPES = pCore.util.Enum("AssetType", ["BasicTransform", "Rig"])
ASSET_MARKER = "AssetDb"
ASSETDB_TYPES = pCore.util.Enum("AssetDbType", ["StaticProp", "DynamicProp"])


class MAsset_OtpVars(object):
    def __init__(self):
        # Duplicate Callback OptVars
        # --------------------------
        if "selectMAssetRoot" not in pCore.env.optionVars:
            pCore.env.optionVars["selectMAssetRoot"] = True

        if "duplicateMAssetCallback" not in pCore.env.optionVars:
            pCore.env.optionVars["duplicateMAssetCallback"] = True

        # Delete Unused Shaders
        # ---------------------
        if not pCore.optionVar.has_key('eMAssetDeleteUnusedShaders'):
            pCore.optionVar['eMAssetDeleteUnusedShaders'] = False

        # Merge Materials OptVars
        # -----------------------
        if not pCore.optionVar.has_key('eMAssetMergeMaterials'):
            pCore.optionVar['eMAssetMergeMaterials'] = True

        if not pCore.optionVar.has_key('eMAssetMergeMaterials_ByDefinition'):
            pCore.optionVar['eMAssetMergeMaterials_ByDefinition'] = True

        if not pCore.optionVar.has_key('eMAssetMergeMaterials_ByName'):
            pCore.optionVar['eMAssetMergeMaterials_ByName'] = False

        if not pCore.optionVar.has_key('eMAssetMergeMaterials_UseSource'):
            pCore.optionVar['eMAssetMergeMaterials_UseSource'] = True

        # Rename OptVars
        if not pCore.optionVar.has_key('eMAssetMaintainRootNames'):
            pCore.optionVar['eMAssetMaintainRootNames'] = True

        if not pCore.optionVar.has_key('eMAssetForceMaintainRootNames'):
            pCore.optionVar['eMAssetForceMaintainRootNames'] = False

    @property
    def selectMAssetRoot_Callback(self):
        return pCore.optionVar['selectMAssetRoot']

    @selectMAssetRoot_Callback.setter
    def selectMAssetRoot_Callback(self, val):
        pCore.optionVar['selectMAssetRoot'] = bool(val)

    @property
    def duplicateMAssetRoot_Callback(self):
        return pCore.optionVar['duplicateMAssetCallback']

    @duplicateMAssetRoot_Callback.setter
    def duplicateMAssetRoot_Callback(self, val):
        pCore.optionVar['duplicateMAssetCallback'] = bool(val)

    @property
    def deleteUnusedShaders(self):
        return bool(pCore.optionVar['eMAssetDeleteUnusedShaders'])

    @deleteUnusedShaders.setter
    def deleteUnusedShaders(self, val):
        pCore.optionVar['eMAssetDeleteUnusedShaders'] = bool(val)

    @property
    def mergeMaterials(self):
        return pCore.optionVar['eMAssetMergeMaterials']

    @mergeMaterials.setter
    def mergeMaterials(self, val):
        pCore.optionVar['eMAssetMergeMaterials'] = bool(val)

    @property
    def mergeMaterialsByDefinition(self):
        return pCore.optionVar['eMAssetMergeMaterials_ByDefinition']

    @mergeMaterialsByDefinition.setter
    def mergeMaterialsByDefinition(self, val):
        pCore.optionVar['eMAssetMergeMaterials_ByDefinition'] = bool(val)

    @property
    def mergeMaterialsByName(self):
        return pCore.optionVar['eMAssetMergeMaterials_ByName']

    @mergeMaterialsByName.setter
    def mergeMaterialsByName(self, val):
        pCore.optionVar['eMAssetMergeMaterials_ByName'] = bool(val)

    @property
    def mergeMaterialsUseSource(self):
        return pCore.optionVar['eMAssetMergeMaterials_UseSource']

    @mergeMaterialsUseSource.setter
    def mergeMaterialsUseSource(self, val):
        pCore.optionVar['eMAssetMergeMaterials_UseSource'] = bool(val)

    @property
    def maintainRootNames(self):
        return pCore.optionVar['eMAssetMaintainRootNames']

    @maintainRootNames.setter
    def maintainRootNames(self, val):
        pCore.optionVar['eMAssetMaintainRootNames'] = bool(val)

    @property
    def forceMaintainRootNames(self):
        return pCore.optionVar['eMAssetForceMaintainRootNames']

    @forceMaintainRootNames.setter
    def forceMaintainRootNames(self, val):
        pCore.optionVar['eMAssetForceMaintainRootNames'] = bool(val)


MASSET_OPT_VARS = MAsset_OtpVars()


class AssetCallbacks(object):
    '''
    This object registers 3 callbacks that run when pre duplicate, new dagNode created
    and post duplicate.  The combination of these callbacks manage MAsset Duplication and
    Make sure that when a duplicate call is committed by code or the user that MAssets
    get duplicated in a particular way.  The callbacks MCallbackId objects are stored as
    a global in the Maya __main__ python scope.  If this variable if filled then when this
    object is created the __remove() method will be run to ensure I copy of these callbacks
    exists
    '''

    def __new__(cls, *args, **kwargs):
        if getattr(__main__, "_AssetCallbacks", None):
            obj = object.__new__(cls, *args, **kwargs)
            obj._create = False
        else:
            obj = object.__new__(cls, *args, **kwargs)
            obj._create = True
        return obj

    def __init__(self):
        self._doingDup = False
        self._addedNodes = []
        self.__enableMAssetDup = True

        if "selectMAssetRoot" not in pCore.env.optionVars:
            pCore.env.optionVars["selectMAssetRoot"] = False
            self.__enableMAssetSel = False
        else:
            # self.__enableMAssetSel = pCore.env.optionVars["selectMAssetRoot"]
            # Hard code this feature off for now.
            pCore.env.optionVars["selectMAssetRoot"] = False
            self.__enableMAssetSel = pCore.env.optionVars["selectMAssetRoot"]

        if "duplicateMAssetCallback" not in pCore.env.optionVars:
            pCore.env.optionVars["duplicateMAssetCallback"] = True
            self.__enableMAssetDup = True
        else:
            self.__enableMAssetDup = pCore.env.optionVars["duplicateMAssetCallback"]
            self.__enableMAssetDup = False

        if self._create:
            self.__create()
        else:
            self.__remove()
            self.__create()

    def setAllCallbacksEnabled(self, value):
        '''
        We can turn off the callbacks that handle MAsset Duplication by setting this var
        :param value: `bool`
        :return:
        '''
        self.setMAssetRootSelectEnabled(value)
        self.setMAssetDuplicateEnabled(value)

    def setMAssetDuplicateEnabled(self, value):
        v = bool(value)
        pCore.env.optionVars["duplicateMAssetCallback"] = v
        self.__enableMAssetDup = v

    def getMAssetDuplicateState(self):
        return pCore.env.optionVars["duplicateMAssetCallback"]

    def setMAssetRootSelectEnabled(self, value):
        v = bool(value)
        pCore.env.optionVars["selectMAssetRoot"] = v
        self.__enableMAssetSel = v

    def getMAssetRootSelectState(self):
        return pCore.env.optionVars["selectMAssetRoot"]

    @classmethod
    def filterSelectionForRoots(cls):
        """Converts the current selection to only have the MAsset Roots selected"""
        preSel = set(pCore.cmds.ls(sl=True))
        roots = set()
        deselect = set()
        for n in preSel:
            if MAsset.IsAssetMember(n):
                Asset = MAsset.GetMAsset(n)
                roots.add(Asset.GetRootTransform())
                deselect.add(n)
        toSel = list(preSel - deselect)
        toSel += list(roots)
        pCore.select(toSel)

    def __repr__(self):
        return 'MAssetDuplicateCallback(%s,%s,%s)' % (self._preDupId, self._dupId, self._postDupId)

    def _preDup(self, *args):
        '''
        Removes any sub MAsset members from the selection and instead adds the Root
        to the selection.  This enforce entire MAsset duplication
        '''
        self._doingDup = True
        if self.__enableMAssetDup:
            self._addedNodes = []

            self.filterSelectionForRoots()

    def __isSelect(self):
        return "select" in pCore.undoInfo(q=True, undoName=True)

    def _outlinerHack(self):
        try:
            pCore.mel.eval("outlinerEditor -e -sc 1  outlinerPanel1;")
        except:
            pass

    def _selectMAsstRoot(self, *args):
        # HARDCODED OFF
        self.__enableMAssetSel = False

        if self.__enableMAssetSel and self.__isSelect():
            self.__enableMAssetSel = False
            selection = pCore.cmds.ls(sl=True, l=True)  # must maintain selection order (don't convert to set)
            removeSel = set()
            addSel = set()

            for node in selection:
                componentTransform = None
                attr = "%s.%s" % (node, "MAsset_Part")
                if pCore.cmds.objExists(attr):
                    partData = json.loads(pCore.cmds.getAttr(attr))
                    if not partData["Root"]:
                        if componentTransform:
                            asset = MAsset_GetMAssetFrom(componentTransform)
                        else:
                            asset = MAsset_GetMAssetFrom(node)
                        if asset:
                            root = MAsset_GetRootTransform(asset)
                            removeSel.add(node)
                            addSel.add(root)

            # if there was no MAsset Components selected then don't do anything.
            # and maintain the original selections

            if addSel or removeSel:
                # this is bad.  sets would have been faster by order of magnitudes!
                remSel = list(removeSel)
                for i in remSel:
                    if i in selection:
                        selection.remove(i)
                selection = selection + list(addSel)

                if selection:
                    pCore.select(selection)

            self.__enableMAssetSel = True

    def _dup(self, node, dummy):
        '''
        Monitors the new nodes added if this is due to a duplicate call
        '''
        if self._doingDup and self.__enableMAssetDup:
            nodePath = om.MDagPath()
            om.MDagPath.getAPathTo(node, nodePath)
            self._addedNodes += [nodePath]

    def _postDup(self, *args):
        '''
        As all MAssets should get a unique UUID on creation we can use this UUID as
        a means to re-compile duplicated Assets into new Assets
        '''

        split = str.split
        self._doingDup = False
        if self.__enableMAssetDup:
            # Loop over all the new nodes created by doing the duplicate.
            # If the new nodes came from a MAsset then it will have a MAsset_Part attribute
            # with a UUID key in the data
            # We record the UUID as a key in a master dict, and record the members of the MAsset in a list
            # EG {"06e5b654-37f4-4224-adcc-f1a2da5e5117":[(nt.Transform(pCube1), {}),]}
            # This gives us a table of new MAssets that need to be recreated by UUID.  We just
            # have to search all the MAssets by UUID and relink them
            UUIDMAssetDict = {}
            for nodePath in self._addedNodes:
                path = nodePath.fullPathName()
                attr = "%s.%s" % (path, "MAsset_Part")
                if pCore.cmds.objExists(attr):
                    partData = json.loads(pCore.cmds.getAttr(attr))
                    if partData.has_key("UUID"):
                        UUID = partData["UUID"]
                        UUIDMAssetDict.setdefault(UUID, [])
                        UUIDMAssetDict[UUID].append((pCore.PyNode(path), partData))
                        # UUIDMAssetDict[UUID].append((path, partData)) # keeping old non pynode version

            if UUIDMAssetDict:  # we did duplicate MAssets

                # build a list of MAssets by UUID.  Ass UUID's are Unique this will be a ever changing list
                # we could potentially cache this and only update if a key isn't found
                UUIDAssets = {}
                MAssets = MAssetUtils.GetAllMAssets(asMetaData=False)
                for a in MAssets:
                    uuid = pCore.getAttr("%s.UUID" % a)
                    UUIDAssets.setdefault(uuid, [])
                    UUIDAssets[uuid].append(a)

                for uuid, data in UUIDMAssetDict.iteritems():
                    _logger.debug("Duplicating MAssets : UUID : %s" % uuid)
                    if UUIDAssets.has_key(uuid):
                        NewAsset = MAsset()
                        OldAsset = MAsset(UUIDAssets[uuid][0])
                        OldAsset.CopyMAssetDbAttrs(NewAsset)

                        renameList = []
                        lod = False
                        for node, partData in data:
                            if node.type() == "lodGroup":
                                lod = node
                                camera = pCore.mel.findStartUpCamera("persp")
                                if camera:
                                    camera = pCore.PyNode(camera)
                                    camera.worldMatrix >> node.cameraMatrix

                            if partData["Root"]:
                                NewAsset.SetRootTransform(node)
                                pCore.select(node, add=True)
                                NewAsset.SetName(pCore.mel.ActualName(node))
                            else:
                                NewAsset.AddAssetMembers(node)
                                renameList.append(node)

                        if lod:
                            oldLodMembers = OldAsset.GetLODMembers()
                            oldLodMeshes = [split(str(m[0].shortName()), "|")[-1] for m in oldLodMembers]
                            oldPlugs = [m[1] for m in oldLodMembers]
                            for newMember in NewAsset.GetAssetMembers():
                                shortName = split(str(newMember.shortName()), "|")[-1]
                                try:
                                    index = oldLodMeshes.index(shortName)
                                    plug = pCore.PyNode("%s.%s" % (lod, oldPlugs[index].name(includeNode=False)))
                                    plug >> newMember.lodVisibility
                                except ValueError:
                                    continue
                                except StandardError, Err:
                                    _logger.exception(Err)

                        NewAsset.EnsureUniqueShortNames(members=renameList, testForUnique=True)

                # A clean up just in case, it seems silly but the more it's run
                # the more likely it's going to be quick.  But I may need to
                # turned off as we're searching metaData a lot.
                MAsset_OptimiseUnused()

    def __remove(self):
        '''
        Important method that tries to remove existing callbacks and re register the new
        callbacks.  Great for code changes where a reload() at module level is called.
        This means code in this object is refreshed.
        '''
        if __main__._AssetCallbacks:
            for c in __main__._AssetCallbacks:
                om.MMessage.removeCallback(c)
                _logger.info('Callbacks Removed : %s' % c)
            __main__._AssetCallbacks = None

    def __create(self):
        self._preDupId = om.MModelMessage.addBeforeDuplicateCallback(self._preDup)
        self._dupId = om.MDGMessage.addNodeAddedCallback(self._dup, 'dagNode')
        self._postDupId = om.MModelMessage.addAfterDuplicateCallback(self._postDup)
        self._selMAssetId = om.MModelMessage.addCallback(om.MModelMessage.kActiveListModified, self._selectMAsstRoot)
        __main__._AssetCallbacks = (self._preDupId, self._dupId, self._postDupId, self._selMAssetId)


# This is the main duplicate callback.  It's created here so the callback exists in
# maya when this module is loaded.  We can also reference this callback global to
# decide what to do in the module.  IE, if _MASSET_CALLBACKS: duplicate()
global _CALLBACK_MANAGER
_CALLBACK_MANAGER = AssetCallbacks()

# _MAssetDagMenu = core.uiTools.DagMenuTrigger()
# _MAssetDagMenu.setTriggerMenuName("e:MAsset")
# _MAssetDagMenu.setAsSubMenu(True)
# _MAssetDagMenu.addMenu("Duplicate MAsset", "MAsset_Rmb_Duplicate")
# _MAssetDagMenu.addMenu("Divider", "")
# _MAssetDagMenu.addMenu("Update MAsset", "MAsset_Rmb_UpdateAsset")
# _MAssetDagMenu.addMenu("Update All MAssets with Id", "MAsset_Rmb_UpdateAllUnderMouseById")
# _MAssetDagMenu.addMenu("Divider", "")
# _MAssetDagMenu.addMenu("Select All Roots with Id", "MAsset_Rmb_SelectAllRootTransformsById")
# _MAssetDagMenu.addMenu("Select RootTransform", "MAsset_Rmb_SelectRootTransform")
# _MAssetDagMenu.addMenu("Select AssetMembers", "MAsset_Rmb_SelectAssetMembers")
# _MAssetDagMenu.addMenu("Select NonRootTransforms", "MAsset_Rmb_SelectNonRootMembers")
# _MAssetDagMenu.addMenu("Divider", "")
# _MAssetDagMenu.addMenu("Disolve MAsset", "MAsset_Rmb_Dissolve")
# _MAssetDagMenu.addMenu("Divider", "")
# _MAssetDagMenu.addMenu("Select MAsset", "MAsset_Rmb_SelectMAsset")


def withLogLevel(level):
    '''
    Decorator for changing the level of prints in the maya script editor
    :param level: int 10-50
    '''

    def wrap(func):
        currentLevel = pCore.nt._logger.getEffectiveLevel()

        def wrappedFunc(*args, **kw):
            pCore.nt._logger.setLevel(level)
            try:
                res = func(*args, **kw)
                pCore.nt._logger.setLevel(currentLevel)
                return res
            except StandardError, Err:
                pCore.nt._logger.setLevel(currentLevel)
                _logger.exception(Err)
                raise Err

        return wrappedFunc

    return wrap


# def UpdateAllMAssetMenus(onReferenced=False):
#    '''
#    iterates over all the non referenced MAssets and updates the menu serialised into the MAsset with
#    this modulesMenu
#    :return:
#    '''
#    for ma in MAssetUtils.GetAllMAssets():
#        if onReferenced:
#            _MAssetDagMenu.serialize(ma.MetaNode)
#        else:
#            if not ma.MetaNode.isReferenced():
#                _MAssetDagMenu.serialize(ma.MetaNode)


# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------

# ALL MEL Wrapped functions must be in the root of the modules to be wrapped
# and then added to the global MEL_WRAP_FUNCTIONS defined at the bottom

# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# Filter Methods
# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------

def MAssetGlobalOptionsDialog():
    import tdtools.tools.assetBrowser as AssetBrowser
    import mQt.core as ui
    ui.Display(AssetBrowser.AssetOptions.AssetOptionsDialog, DeleteExisting=True)


def Install_FilterArray_RootTransform_MelProcedure():
    '''
    Because we can't register python methods that take string[] to the mel world
    I'm using a hand crafted proc that I'm evaluating here
    :return: None
    '''

    cmd = '''
   global proc string[] FilterArray_RootTransform (string $nodes[])
   {
         string $stringArray;
         string $res[];
         $stringArray = `stringArrayToString $nodes ","`;
         $res = MAsset_FilterArray_RootTransform($stringArray);
         return $res;
   }
   '''
    pCore.mel.eval(cmd)


def Masset_FilterOutliner():
    '''
    Method to filter out Non root members from the outliner
    :return:
    '''

    if pCore.objExists("AssetItemFilter"):
        pCore.delete("AssetItemFilter")

    assetFiler = pCore.itemFilter("AssetItemFilter", ss="FilterArray_RootTransform", unn=True)
    pCore.outlinerEditor("outlinerPanel1", e=True, filter=assetFiler)


def MAsset_ToggleFilterOutliner():
    if pCore.objExists("AssetItemFilter"):
        pCore.delete("AssetItemFilter")
        pCore.mel.filterUIClearFilter("outlinerPanel1")
    else:
        Masset_FilterOutliner()


def MAsset_FilterArray_RootTransform(nodes):
    if isinstance(nodes, basestring):
        nodes = nodes.split(",")
    remove = set()
    for n in nodes:
        if MAsset_FilterNonRootTransform(n):
            remove.add(n)
    res = set(nodes)
    res -= remove
    return list(res)


def MAsset_FilterRootTransform(name):
    '''
    Filter method for use in the outliner or with itemFilters

    .. example:

        assetFiler = pCore.itemFilter("AssetFilterNew", byScript="MAsset_RootTransformFilter", unn=True)

        # add the filter to the outliner
        pCore.outlinerEditor("outlinerPanel1", e=True, filter=assetFiler)

        roots = pCore.lsThroughFilter(assetFiler)

    :param name: longName oo node
    :return: `bool`
    '''

    if MAsset_IsRootTransform(name):
        return 1
    else:
        return 0


def MAsset_FilterNonRootTransform(name):
    '''
    Filter method for use in the outliner or with itemFilters

    .. example:

        assetFiler = pCore.itemFilter("AssetFilterNew", byScript="MAsset_NonRootTransformFilter", unn=True)

        # add the filter to the outliner
        pCore.outlinerEditor("outlinerPanel1", e=True, filter=assetFiler)

        roots = pCore.lsThroughFilter(assetFiler)

    :param name: longName oo node
    :return: `bool`
    '''
    attr = MAsset_GetMAssetPartAttr(name)
    if attr:
        if not MAsset_IsRootTransform(name):
            return 1
        else:
            return 0
    else:
        if pCore.objectType(name) == "mesh":
            name = pCore.PyNode(name).getParent().name()
            attr = MAsset_GetMAssetPartAttr(name)
            if attr:
                if not MAsset_IsRootTransform(name):
                    return 1
                else:
                    return 0
        return 0


# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------


def MAsset_DuplicateSelectedAssets(select=True):
    '''
    Will Duplicate the selected MAssets in the Scene
    :return:
    '''
    preSel = pCore.cmds.ls(sl=True)
    Assets = set()
    res = []
    for n in preSel:
        if MAsset.IsAssetMember(n):
            Assets.add(MAsset.GetMAsset(n))
    for a in Assets:
        res.append(a.DuplicateAsset())
    if select:
        for a in res:
            pCore.select(a.GetRootTransform(), add=True)
    return res


def MAsset_OptimiseUnused():
    '''
    Wrapped to MEL.

    Paranoid mind,  I bet that there will be MAssets in the scene that have to connections to
    Members.  This will delete these from the scene
    '''
    opt = 0
    for i, n in enumerate(pCore.cmds.ls(type="network")):
        if pCore.cmds.objExists("%s.metaClass" % n):
            klassName = pCore.cmds.getAttr("%s.metaClass" % n)
            if klassName == "MAsset":
                if not metaData.IsValidMetaNode(n):
                    pCore.delete(n)
                    opt += 1
    _logger.info("Optimised %s MAsset Node" % opt)


def MAsset_GetMAssetFrom(Node):
    '''
    Wrapped to MEL.

    :returns: `str` MAsset metaNode attached to the given Node
    '''
    if isinstance(Node, pCore.PyNode):
        Node = Node.longName()
    metaNodes = [n for n in pCore.cmds.listConnections(Node, s=1, d=0, type="network") if
                 pCore.cmds.objExists("%s.metaClass" % n)]
    if metaNodes:
        nodes = [n for n in metaNodes if pCore.cmds.getAttr("%s.metaClass" % n) == "MAsset"]
        if nodes:
            return nodes[0]
        return ""
    return ""


def MAsset_GetNonRootMembers(MAssetNode):
    '''
    Wrapped to MEL.

    Given a metaNode of type MAsset will return a all Non Root Asset Members

    :param MAssetNode: `str` metaNode
    :returns: [str,]
    '''
    if pCore.cmds.objectType(MAssetNode) == "network":
        if pCore.cmds.objExists("%s.metaClass" % MAssetNode):
            if pCore.cmds.getAttr("%s.metaClass" % MAssetNode) == "MAsset":
                return [str(m) for m in MAsset(MAssetNode).GetNonRootMembers()]
            else:
                return ["", ]
        return ["", ]
    else:
        return ["", ]


def MAsset_GetRootTransform(MAssetNode):
    '''
    Wrapped to MEL.

    Given a metaNode of type MAsset will return the RootTransforms

    :param MAssetNode: `str` metaNode
    :returns: `str`
    '''
    if pCore.cmds.objectType(MAssetNode) == "network":
        if pCore.cmds.objExists("%s.metaClass" % MAssetNode):
            if pCore.cmds.getAttr("%s.metaClass" % MAssetNode) == "MAsset":
                root = MAsset(MAssetNode).GetRootTransform()
                if root:
                    return str(root)
                else:
                    return ""
            else:
                return ""
        return ""
    else:
        return ""


def MAsset_IsRootTransform(name):
    '''
    :param name: `str` object longName
    :return: `bool`
    '''

    attr = MAsset_GetMAssetPartAttr(name)
    if attr:
        partData = json.loads(pCore.cmds.getAttr(attr))
        if partData.has_key("Root"):
            if partData["Root"]:
                return True
            else:
                return False
        else:
            return False
    return False


def MAsset_GetMAssetPartAttr(name):
    '''
    Only check if the MAsset_Part attribute exists on the node
    :param name: `str` longName of node
    :return: `bool`
    '''

    attr = "%s.%s" % (name, "MAsset_Part")
    if pCore.cmds.objExists(attr):
        return attr


def MAsset_Dissolve_Selected():
    '''
    User selects items in the scene that maya be MAssets and we filter for Assets from the
    Selected and then Dissolve them.
    '''

    mAssetsSet = set()
    for node in pCore.selected():
        mAssetsSet.add(MAsset_GetMAssetFrom(node))

    for mA in mAssetsSet:
        mA = MAsset(mA)
        mA.Dissolve()


def MAsset_PushChangesBackToSource_Selected():
    '''
    User selects items in the scene that maya be MAssets and we filter for Assets from the
    Selected and then Push any changes back into the source files
    '''

    mAssetsSet = set()
    for node in pCore.selected():
        mAssetsSet.add(MAsset_GetMAssetFrom(node))

    for mA in mAssetsSet:
        mA = MAsset(mA)
        mA.PushEditsBackToSource()


def RBM_Decorator_ToMAsset(func):
    def inner(asset):
        assetNode = MAsset_GetMAssetFrom(asset)
        if assetNode:
            Asset = MAsset(assetNode)
            return func(Asset)
        else:
            raise TypeError("Node %s has no MAsset" % asset)

    inner.__name__ = func.__name__
    return inner


@RBM_Decorator_ToMAsset
def MAsset_Rmb_UpdateAsset(Asset):
    '''
    Updates just the MAsset under the mouse
    '''
    AssetObj = MAssetUtils.GetDataBaseAssetObject(Asset.id)
    MAssetUtils.UpdateAssets([Asset, ], AssetObj)


@RBM_Decorator_ToMAsset
def MAsset_Rmb_OpenSource(Asset):
    '''
    Opens the MAsset Under the Mouse
    '''
    MAssetUtils.OpenMAssetSource(Asset)


@RBM_Decorator_ToMAsset
def MAsset_Rmb_UpdateAllUnderMouseById(Asset):
    '''
    Updates just the MAsset with the same ID and the input Asset
    '''
    AssetObj = MAssetUtils.GetDataBaseAssetObject(Asset.id)
    Assets = MAssetUtils.GetMAssetsBy_DatabaseId(Asset.id)
    MAssetUtils.UpdateAssets(Assets, AssetObj)


@RBM_Decorator_ToMAsset
def MAsset_Rmb_SelectAllRootTransformsById(Asset):
    '''
    Select just the RootTransforms with the same ID and the input Asset
    '''
    Assets = MAssetUtils.GetMAssetsBy_DatabaseId(Asset.id)
    pCore.select(cl=True)
    for a in Assets:
        pCore.select(a.GetRootTransform(), add=True)


@RBM_Decorator_ToMAsset
def MAsset_Rmb_SelectMAsset(Asset):
    Asset.m_Select()


@RBM_Decorator_ToMAsset
def MAsset_Rmb_SelectRootTransform(Asset):
    pCore.select(Asset.GetRootTransform())


@RBM_Decorator_ToMAsset
def MAsset_Rmb_SelectAssetMembers(Asset):
    pCore.select(Asset.GetAssetMembers())


@RBM_Decorator_ToMAsset
def MAsset_Rmb_SelectNonRootMembers(Asset):
    pCore.select(Asset.GetNonRootMembers())


@RBM_Decorator_ToMAsset
def MAsset_Rmb_Duplicate(Asset):
    newAsset = Asset.DuplicateAsset()


@RBM_Decorator_ToMAsset
def MAsset_Rmb_Dissolve(Asset):
    '''
    Completely remove the MAsset system from the respective Nodes
    :param Asset: str MayaNode under pointer
    :return:
    '''
    Asset.Dissolve()


class PolyGrpInPlace(object):
    def __init__(self):
        self.baseObjParent = None
        self.sel = []
        self.origSel = pCore.ls(sl=True, fl=True)
        self.listPos = None

    def reset(self, *args):
        self.baseObjParent = None
        self.sel = []
        self.origSel = pCore.ls(sl=True, fl=True)
        self.listPos = None

    def getEntity(self, n):
        for i in n.getAllParents():
            if "_VRT" in str(i).upper() or "_LMP" in str(i).upper():
                return i

    def main(self, *args):
        self.reset()

        if len(self.origSel) > 0:
            pCore.select(self.origSel[0])
            AssetCallbacks.filterSelectionForRoots()

            baseName = pCore.selected()[0].shortName()
            self.baseObjParent = self.getEntity(pCore.selected()[0])
            if not self.baseObjParent:
                pCore.select(self.origSel)
                raise StandardError("Incorrectly named entity, looking for suffix '_VRT' or '_LMP'")

            pCore.select(self.origSel)

            AssetCallbacks.filterSelectionForRoots()

            self.sel = pCore.selected()

            if self.baseObjParent != None:
                rels = self.baseObjParent.listRelatives()
                if baseName in rels:
                    self.listPos = rels.index(baseName)

            pCore.group(self.sel)
            polyGrp = pCore.selected()[0]
            polyGrp.rename(
                self.baseObjParent.shortName().split("_")[0] + "_" + self.baseObjParent.shortName().split("_")[
                    1] + "_" + "Props_PolyGrp")
            pCore.parent(self.sel, polyGrp)

            try:
                pCore.parent(polyGrp, self.baseObjParent)
            except:
                pass

            if self.baseObjParent != None:
                pCore.reorder(polyGrp, front=True)
                pCore.reorder(polyGrp, relative=self.listPos)
        else:
            pCore.warning("Nothing selected")


def SelectionToMergePolyGroup():
    """
    User makes a selection of transforms in the scene and then the selection is grouped under a
    mergePolyGroup transform (at 1st selected objects dag outliner position) node that is used my EL4 on import to reduce batches.
    :return: None
    """
    obj = PolyGrpInPlace()
    obj.main()


class MAssetUtils:
    """
    Useful Methods to work with MAssets
    """

    @classmethod
    def GetAllMAssets(cls, GroupById=False, UUID="", asMetaData=True):
        if not GroupById:
            return [m for m in metaData.IterMetaNodesForClass(MAsset, asMetaData=asMetaData)]
        elif UUID:
            toReturn = []
            assetIdDict = {}
            for m in metaData.IterMetaNodesForClass(MAsset, asMetaData=False):
                uuid = pCore.getAttr("%s.UUID" % m)

                if asMetaData:
                    m = MAsset(m)

                assetIdDict.setdefault(str(uuid), [])
                assetIdDict[str(uuid)].append(m)

            for key in sorted(assetIdDict):
                toReturn.append((key, assetIdDict[key]))
            return toReturn
        else:
            toReturn = []
            assetIdDict = {}
            for m in metaData.IterMetaNodesForClass(MAsset, asMetaData=False):
                try:
                    # Id's may not exists if they are not imported from the browser but rather just
                    # created with the MAsset Editor
                    idAttr = pCore.getAttr("%s.id" % m)
                    if asMetaData:
                        m = MAsset(m)
                    assetIdDict.setdefault(str(idAttr), [])
                    assetIdDict[str(idAttr)].append(m)
                except StandardError, Err:
                    if not isinstance(Err, pCore.MayaAttributeError):
                        raise Err

            for key in sorted(assetIdDict):
                toReturn.append((key, assetIdDict[key]))
            return toReturn

    @classmethod
    def GetMAssetsBy_DatabaseId(cls, idx):
        return [m for m in metaData.IterMetaNodesForClass(MAsset) if getattr(m, "id", None) == idx]

    @classmethod
    def GetDataBaseAssetObject(cls, idx):
        import tdtools.assetSpider.astDb as astDb
        return astDb.AssetDbHelper().getAssetFromId(idx)

    @classmethod
    def AutoAssetImportedNodes(cls, ImportedNodes, namespace, name):
        """
        From the nodes imported now build the asset up
        :param ImportedNodes: [PyNode,]
        :param namespace: ""
        :param name: AssetName
        :return: mAsset, [new imported assets]
        """
        ignoreTypes = ["camera"]

        transforms = []
        deletedNodes = set()
        ImportedNodes = set(ImportedNodes)
        for n in ImportedNodes:
            if pCore.objectType(n) == "transform":
                children = pCore.listRelatives(n)
                passed = True
                for obj in children:
                    if pCore.objectType(obj) in ignoreTypes:
                        deletedNodes.add(n)
                        passed = False
                if passed:
                    transforms.append(n)
            elif pCore.objectType(n) == "lodGroup":
                transforms.append(n)

        ns = namespace
        name = "%s:%s" % (ns, name)
        Asset = MAsset(Name=name)
        Asset.AddAssetMembers(transforms)
        Asset.AutoSetRoot()

        ImportedNodes = ImportedNodes - deletedNodes
        pCore.delete(deletedNodes)

        ImportedNodes.add(Asset.MetaNode)
        Asset.SetName(name + "_ASS")
        return Asset, list(ImportedNodes)

    @classmethod
    def ImportAutoAsset(cls, ImportedNodes, AssetObj):
        ignoreTypes = ["camera"]

        transforms = []
        deletedNodes = set()
        ImportedNodes = set(ImportedNodes)
        for n in ImportedNodes:
            if pCore.objectType(n) == "transform":
                children = pCore.listRelatives(n)
                passed = True
                for obj in children:
                    if pCore.objectType(obj) in ignoreTypes:
                        deletedNodes.add(n)
                        passed = False
                if passed:
                    transforms.append(n)
            elif pCore.objectType(n) == "lodGroup":
                transforms.append(n)

        ns = getattr(AssetObj, "namespace", "")
        name = "%s:%s" % (ns, AssetObj.name)
        Asset = MAsset(Name=name)
        Asset.AddAssetMembers(transforms)
        Asset.AutoSetRoot()

        ImportedNodes = ImportedNodes - deletedNodes
        pCore.delete(deletedNodes)

        ImportedNodes.add(Asset.MetaNode)
        Asset.SetName(AssetObj.name)
        return list(ImportedNodes)

    @classmethod
    def AutoAssetScene(cls, deleteUnwanted=True, rootNode=None, useRootName=True):
        with pCore.UndoChunk():
            if MAssetUtils.GetAllMAssets():
                raise StandardError("There are already MAssets in the scene, Can't create a MAsset")
            nodes = [t.getParent() for t in pCore.ls(et="mesh")]
            nodes.extend(pCore.ls(et="lodGroup"))
            pCore.select(nodes)
            Asset = MAsset(Selection=True)

            if deleteUnwanted:
                roots = set()
                for n in pCore.ls(et="transform"):
                    roots.add(n.root())

                aRoot = Asset.GetRootTransform()
                if len(roots) > 1:
                    for r in roots:
                        if r != aRoot:
                            s = r.getShape()
                            if not s:
                                try:
                                    pCore.delete(r)
                                except:
                                    pass
            if rootNode:
                rootNode = pCore.PyNode(rootNode)
                Asset.SetRootTransformPivot(rootNode.getPivots(ws=True)[0], ws=True)
                if useRootName:
                    Asset.GetRootTransform().rename(rootNode + "_mAss")

            return Asset

    @classmethod
    def OpenMAssetSource(cls, mAsset, force=True):
        path = ""
        if isinstance(mAsset, MAsset):
            mAsset = mAsset.MetaNode
            path = mAsset.assetPath.get()
        else:
            try:
                mAsset = pCore.PyNode(mAsset)
                path = mAsset.assetPath.get()
            except:
                path = str(mAsset)

        path = pCore.util.path(path)
        path = path.abspath()

        if path.exists():
            if force:
                from mQt import QtGui
                import mQt.core as ui

                if pCore.cmds.file(q=1, amf=1):
                    maya = ui.getMayaMainWindow()
                    ret = QtGui.QMessageBox.warning(maya, "Open Asset Warning",
                                                    "The maya document has been modified.\nThus may need saving\n"
                                                    "Are you sure you want to open this Asset?",
                                                    QtGui.QMessageBox.Open | QtGui.QMessageBox.Cancel)
                    if ret == QtGui.QMessageBox.Open:
                        tdtools.core.fileTools.Loader.LoadFile(path, tdtools.core.fileTools.OpenMode.Open)
                        tdtools.core.general.addToRecentOpenList(path)
            else:
                tdtools.core.fileTools.Loader.LoadFile(path, tdtools.core.fileTools.OpenMode.Open)
                tdtools.core.general.addToRecentOpenList(path)

    @classmethod
    def MergeMAssetMaterials(cls, MAssetObj, **kwargs):

        import tdtools.assetSpider.mayaMaterialSpider as MayaMaterialSpider

        errors = []

        def matchMaterials(searchName, sceneMaterials):
            """
            This is the main method for matching by name
            """
            materialsStartWith = (oM for oM in sceneProcessMaterials if oM.name().startswith(searchName))
            # Say our material without a trailing number is FOO
            # this will find all materials that start with FOO but FOOBAR is still valid and we don't want them
            # So now we have to loop over the materials an try to see if the remaing chars convert to a int.
            # if they do then add them
            res = []
            for m in materialsStartWith:
                materialName = m.stripNum()
                if materialName == searchName:
                    res.append(m)
            return res

        def inValidIncomingMaterialName(seq):
            """
            Material names are invalid if there are 2 materials with the same name without the trailing numbers
            IE Brick01 and Brick02 in a scene would mean both these materials will get merged to Brick
            """
            seen = set()
            seq = list(seq)
            seen_add = seen.add
            result = [x for x in seq if x not in seen and not seen_add(x)]
            return len(result) == len(seq)

        kwargs.setdefault("mergeByName", True)
        kwargs.setdefault("mergeUseSource", MASSET_OPT_VARS.mergeMaterialsUseSource)

        kwargs["mergeByName"] = True  # HardCoded on as the material database isn't there.

        invalidMaterialConvention = False

        if kwargs["mergeByName"]:
            _logger.info("Merging Using Name Matching")
            _logger.info("Merging Using Source Material : %s" % kwargs["mergeUseSource"])
            assetProcessMaterials = set(MAssetObj.GetMaterials())
            _logger.debug("Materials from MASSET : %s" % pformat(assetProcessMaterials))
            if not inValidIncomingMaterialName([n.stripNum() for n in assetProcessMaterials]):
                errorString = """Invalid Naming Convention Used in Incomming Materials from %s""" % MAssetObj
                errorString += "\nIE Brick01, Brick02,  Please use alphabetic suffix to denote versioning... BrickA, BrickB etc"
                errorString += "\nThere is a very good chance that these materials wont get merged correctly and Brick02 will become Brick\n\n"
                errors.append(errorString)
                _logger.critical(errorString)
                invalidMaterialConvention = True

            # allMaterials = set([m for m in MayaMaterialSpider.gMatHelper.GetMayaMaterials()])
            allMaterials = set([m for m in pCore.ls(mat=True)])
            sceneProcessMaterials = allMaterials - assetProcessMaterials
            _logger.debug("Scene Materials > %s" % pformat(sceneProcessMaterials))

            for m in assetProcessMaterials:
                rename = False
                newName = ""

                nameWithoutNumber = m.stripNum()
                nameMatchedMaterials = matchMaterials(nameWithoutNumber, sceneProcessMaterials)
                _logger.debug("Matched Materials > %s" % pformat(nameMatchedMaterials))
                if nameMatchedMaterials:
                    _logger.warning("Found Name Matched Material Asset Material:{0}, Scene Material:{1}".format(m,
                                                                                                                nameMatchedMaterials))
                    if kwargs["mergeUseSource"]:
                        _logger.info("Merging Using Source:{0}".format(m))
                        dupList = nameMatchedMaterials
                        toUse = m
                        rename = True
                        newName = nameWithoutNumber
                    else:
                        _logger.info("Merging Using Current File Material:{0}".format(nameMatchedMaterials[0]))
                        dupList = [m]
                        toUse = nameMatchedMaterials[0]

                    MayaMaterialSpider.gMatHelper.RemoveMaterialAndAssignInstead(dupList, toUse)
                    if newName and rename:
                        pCore.PyNode(m).rename(newName)

        else:
            assetProcessMaterials = set(MAssetObj.GetMaterials())
            sceneProcessMaterials = [str(m) for m in MayaMaterialSpider.gMatHelper.GetMayaMaterials()]
            if not sceneProcessMaterials:
                return
            import mQt.core as ui
            with ui.MayaProgressBarManager(len(sceneProcessMaterials), False) as pBar:
                pBar.setText("Checking For Scene Duplicate Materials")
                dupMaterials = MayaMaterialSpider.gMatHelper.GetDuplicateMaterialsFromMaterialList(sceneProcessMaterials,
                                                                                                   None,
                                                                                                   pBar.setValue)
                if dupMaterials:
                    pBar.reset()
                    pBar.setMax(len(dupMaterials))
                    pBar.setText("Merging Duplicate Materials")
                    for i, dupList in enumerate(dupMaterials):
                        pBar.setValue(i + 1)
                        superSet = set(dupList)
                        if assetProcessMaterials.intersection(superSet):
                            # now how do we know which mat to use?
                            # one option would be to bring all the new assets in a temp namespace
                            # then do all the checking then remove the temp namespace
                            shortest = {}
                            toUse = dupList[0]
                            for name in dupList:
                                shortest.setdefault(str(len(name)), [])
                                shortest[str(len(name))].append(name)
                            for k in sorted(shortest.keys()):
                                if shortest[k]:
                                    toUse = shortest[k][0]
                                    break
                            try:
                                MayaMaterialSpider.gMatHelper.RemoveMaterialAndAssignInstead(dupList, toUse)
                                _logger.info("Merging materials : using material %s as master material" % toUse)
                            except StandardError, Err:
                                _logger.warning("Failed to merge materials : %s" % toUse)
        return errors

    @classmethod
    def ContaineriseMAsset(cls, MAssetObj):
        '''
        Given a MAsset this will add the AssetMembers to a "Asset with Transform"
        and point the RootTransform MAsset message link to the Maya Asset

        Assets seem to have loads of issues when you want to use Assets like a grouped
        black box piece of geo.  So Currently I can't use Assets.  If I could then I could
        get rid of the Duplicate callback.  Or I could use the Duplicate callback to
        tidy up the Problems with Assets.  I haven't tried this approach yet.

        :param MAssetObj: `MAsset`
        :return: PyNode 'dagContainer'
        '''

        if isinstance(MAssetObj, basestring):
            MAssetObj = pCore.PyNode(MAssetObj)
        elif isinstance(MAssetObj, pCore.PyNode):
            if MAssetObj.type() == 'metaNode':
                if MAssetObj.metaClass.get() == MAsset.__class__.__name__:
                    MAssetObj = metaData.MetaData(MAssetObj)

        if not isinstance(MAssetObj, MAsset):
            raise TypeError("Expected a str or PyNode or MAsset instance")

        Root = MAssetObj.GetRootTransform()
        if Root and Root.type() != 'dagContainer':
            nodes = MAssetObj.GetAssetMembers()
            nodes.append(MAssetObj.MetaNode)
            dagAsset = pCore.container(addNode=nodes,
                                       typ='dagContainer',
                                       includeShapes=True,
                                       includeNetwork=True,
                                       includeHierarchyBelow=True,
                                       includeTransform=True,
                                       force=True)
            dagAsset.blackBox.set(True)
            dagAsset.setRotatePivot(Root.getRotatePivot(sapce='world'))
            MAssetObj.SetRootTransform(dagAsset)
        else:
            raise StandardError("You can't container a dagContainer or a MAsset without a Root")
        return dagAsset

    @classmethod
    def MergeImportedLayers(cls, newNodes):
        '''
        Given new nodes from a import this will merge the layers from the new nodes
        to the current layers that have the same name.  The comparison isn't case sensitive
        :param newNodes: [str,str]
        :return: None
        '''
        newLayers = set([l.name() for l in newNodes if pCore.objectType(l) == "displayLayer"])
        oldLayers = set(pCore.cmds.ls(type="displayLayer")) - newLayers
        for l in oldLayers:
            for nl in newLayers:
                if nl.upper().startswith(l.upper()):
                    newNodes.remove(nl)
                    cls.MergeLayer(l, nl)
        return newNodes

    @classmethod
    def MergeLayer(cls, KeepLayer, DeleteLayer):
        """
        Expects 2 displayLayers and puts the contents of the DeleteLayer into the KeepLayer

        :param KeepLayer: str or PyNode of displacyLayer
        :param DeleteLayer: str or PyNode of displacyLayer
        :return: None
        """
        members = pCore.editDisplayLayerMembers(DeleteLayer, q=True, fn=True)
        pCore.editDisplayLayerMembers(KeepLayer, members)
        pCore.delete(DeleteLayer)

    @classmethod
    def RemoveUnwantedNodesFromImport(cls, newNodes):
        import pprint
        import tdtools.core.health as health
        # import tdtools.assetSpider.mayaMaterialSpider as MayaMaterialSpider

        cleanFromImport = ["initialVertexBakeSet", "vertexBakeSet", "cameraView", "imagePlane"]
        # cameraViews have 1 connection
        newNodes = health.DeleteUnusedNodes(newNodes, typesFilter=cleanFromImport, minConnections=1,
                                            returnType="remaining")

        def filterFor(newNodes, filters=[], methods=[]):
            removed = []
            if filters:
                for n in newNodes:
                    if pCore.objExists(n):
                        objType = pCore.objectType(n)
                        if objType in filters:
                            methodIndex = filters.index(objType)
                            removed.append(methods[methodIndex](n))
            if any(removed):
                _logger.info("Removed unwanted nodes from MAsset Import")
                pprint.pprint(removed)

        def _removeUnusedMaterialImports(shadingGroup):
            # if shadingGroup.IsUnused():
            #     mats = shadingGroup.GetConnectedMaterials()
            #     pCore.delete(shadingGroup)
            #     for m in mats:
            #         removed = MayaMaterialSpider.gMatHelper._DeleteUnusedMaterial(m)
            #         return removed
            pass

        def _removeExportTags(metaNode):
            n = str(metaNode)
            if metaData.MetaData.m_MetaNodeIsExportTag(metaNode):
                try:
                    tag = metaData.MetaData(metaNode)

                    # Support for Achi V2 before delete was standardised
                    if getattr(tag, "Delete", None):
                        tag.Delete()
                    else:
                        tag.m_Delete()
                    return n

                except StandardError, Err:
                    _logger.exception(Err)

        removeNodesTypes = ["shadingEngine", "metaNode", ]
        removeMethods = [_removeUnusedMaterialImports, _removeExportTags]
        filterFor(newNodes, removeNodesTypes, removeMethods)

        # clean up
        return [n for n in newNodes if pCore.objExists(n)]

    @classmethod
    @withLogLevel(50)
    def ImportSceneAssebly(cls, AssetObj, **kwargs):
        assembly = pCore.container(type="assemblyDefinition", name="%s" % (AssetObj.name))
        pCore.mel.assemblyCreateRepresentation("Locator", assembly)
        pCore.mel.assembly(assembly, e=True,
                           createRepresentation="Scene",
                           input=AssetObj.path)
        assembly.representations[1].repLabel.set("Geo")
        assembly.blackBox.set(True)

        ns = AssetObj.namespace
        name = "%s:%s" % (ns, AssetObj.name)
        Asset = MAsset(Name=name)
        Asset.AddAssetMembers(assembly)
        Asset.AutoSetRoot()
        Asset.SetAssetDbObj(AssetObj)

        return [Asset], [assembly]

    @classmethod
    @withLogLevel(50)
    def ImportAssetFromAssetDb(cls, AssetObj, **kwargs):
        '''
        This is the main call from the AssetBrowser that imports the selected Asset

        :param AssetObj: `tdtools.assetSpider.AssetSpider.Asset`
        :param AutoAsset: `bool` runs the logic that Creates MAssets from the imported nodes
        :param MergeMaterials: `bool` runs the MaterialSpider logic for merging materials that are the
                                same from the imported node to the current materials.  The shortest material
                                name is used as the material to keep
        :param DeleteUnused: `bool` runs Maya's MLDeleteUnused material clean-up as post method
        :return: ([MAsset,], [newNode])
        '''
        # return cls.ImportSceneAssebly(AssetObj, **kwargs)
        kwargs.setdefault("deleteUnusedShaders", MASSET_OPT_VARS.deleteUnusedShaders)
        kwargs.setdefault("mergeMaterials", MASSET_OPT_VARS.mergeMaterials)
        kwargs.setdefault("mergeByDefinition", MASSET_OPT_VARS.mergeMaterialsByDefinition)
        kwargs.setdefault("mergeByName", MASSET_OPT_VARS.mergeMaterialsByName)
        kwargs.setdefault("mergeUseSource", MASSET_OPT_VARS.mergeMaterialsUseSource)
        kwargs.setdefault("autoAsset", True)
        kwargs.setdefault("makeContainer", False)

        _logger.info("ImportAssetFromAssetDb : Options {0}".format((kwargs)))

        kw = {}
        nameSpaceSwitch = getattr(AssetObj, "namespace", "")
        if nameSpaceSwitch:
            kw["namespace"] = nameSpaceSwitch
        else:
            kw["defaultNamespace"] = True

        kw["gr"] = False
        kw["rdn"] = False
        kw["loadReferenceDepth"] = "all"
        kw["shd"] = ("displayLayers", "renderLayersByName")
        kw["returnNewNodes"] = True
        _logger.debug("Maya Import : Options {0}".format((kw)))

        newNodes = pCore.importFile(AssetObj.getResolvedPath(), **kw)

        # NOTE: newNodes is a list of PyNodes at this point
        Assets = cls.FindMAssetsIn(newNodes)
        removed = set()

        # Get the layers from the new nodes and merge them based on a name search
        newNodes = cls.MergeImportedLayers(newNodes)

        if kwargs["autoAsset"]:
            if not Assets:
                newNodes = cls.ImportAutoAsset(newNodes, AssetObj)
                Assets = cls.FindMAssetsIn(newNodes)
            else:
                _logger.info("SCENE HAS ASSETS")

        for a in Assets:
            # This records the DataBase info onto the new MAsset.  VERY IMPORTANT PART!!
            assert isinstance(a, MAsset)
            a.SetAssetDbObj(AssetObj)

            ## When all the bug's with Assets are Ironed out we can start to use them,
            ## Pfff.  Not likely if Autodesk have anything to do with it.

            if kwargs["makeContainer"]:
                cls.ContaineriseMAsset(a)

            # Merge any materials from the new MAssets shortest material name is used
            # -----------------------------------------------------------------------
            if kwargs["mergeMaterials"]:
                errors = cls.MergeMAssetMaterials(a, **kwargs)
                if errors:
                    if not core.SCENE.getSuppressWindowState():
                        errorString = ""
                        for m in errors:
                            errorString += "\n" + m
                        pCore.PopupError(errorString)

            a.EnsureUniqueShortNames(testForUnique=True)

        MAsset_OptimiseUnused()
        newNodes = cls.RemoveUnwantedNodesFromImport(newNodes)
        if kwargs["deleteUnusedShaders"]:
            _logger.debug("Deleting Unused Shaders...")
            pCore.evalDeferred(pCore.mel.MLdeleteUnused)
        return Assets, list(newNodes)

    @classmethod
    def AlignPivotAndFreezeChild(ckl, node):
        root = pCore.PyNode(node).root()
        children = root.getChildren(type="transform")
        if children:
            firstChild = pCore.PyNode(children[0])
            refPivots = pCore.xform(firstChild, rp=True, q=True, ws=True)
            pCore.xform(root, ws=True, piv=refPivots)
            pCore.select(root)

    @classmethod
    @withLogLevel(50)
    def ImportAssetFromFilePath(cls, path, assetName, namespace="", **kwargs):
        '''
        This is the main call from the AssetBrowser that imports the selected Asset

        :param AssetObj: `tdtools.assetSpider.AssetSpider.Asset`
        :param AutoAsset: `bool` runs the logic that Creates MAssets from the imported nodes
        :param MergeMaterials: `bool` runs the MaterialSpider logic for merging materials that are the
                                same from the imported node to the current materials.  The shortest material
                                name is used as the material to keep
        :param DeleteUnused: `bool` runs Maya's MLDeleteUnused material clean-up as post method
        :return: ([MAsset,], [newNode])
        '''
        kwargs.setdefault("deleteUnusedShaders", MASSET_OPT_VARS.deleteUnusedShaders)
        kwargs.setdefault("mergeMaterials", MASSET_OPT_VARS.mergeMaterials)
        kwargs.setdefault("mergeByDefinition", MASSET_OPT_VARS.mergeMaterialsByDefinition)
        kwargs.setdefault("mergeByName", MASSET_OPT_VARS.mergeMaterialsByName)
        kwargs.setdefault("mergeUseSource", MASSET_OPT_VARS.mergeMaterialsUseSource)
        kwargs.setdefault("autoAsset", True)
        kwargs.setdefault("makeContainer", False)
        kwargs.setdefault("uniqueNames", False)

        _logger.info("ImportAssetFromFilePath : Options {0}".format(**kwargs))
        Assets = []

        kw = {}
        if namespace:
            kw["namespace"] = namespace
        else:
            kw["defaultNamespace"] = True
        kw["rdn"] = True
        kw["loadReferenceDepth"] = "all"
        kw["shd"] = ("displayLayers", "renderLayersByName")
        kw["returnNewNodes"] = True
        newNodes = pCore.importFile(path, **kw)

        # NOTE: newNodes is a list of PyNodes at this point
        Assets = cls.FindMAssetsIn(newNodes)

        # Get the layers from the new nodes and merge them based on a name search
        newNodes = cls.MergeImportedLayers(newNodes)
        transforms = [n for n in newNodes if n.type() == "transform"]
        roots = [t.root() for t in transforms]

        if kwargs["autoAsset"]:
            if not Assets:
                Asset, newNodes = cls.AutoAssetImportedNodes(newNodes, namespace, assetName)
                Assets = [Asset]
            else:
                _logger.info("SCENE HAS ASSETS")

        for a in Assets:
            # This records the DataBase info onto the new MAsset.  VERY IMPORTANT PART!!
            assert isinstance(a, MAsset)
            data = dict(assetName=assetName,
                        assetPath=path)
            a.setAssetDataDict(data)

            # When all the bug's with Assets are Ironed out we can start to use them,
            # Pfff.  Not likely if Autodesk have anything to do with it.
            # ----------------------------------------------------------------------
            if kwargs["makeContainer"]:
                cls.ContaineriseMAsset(a)

            # Merge any materials from the new MAssets shortest material name is used
            #  -----------------------------------------------------------------------
            if kwargs["mergeMaterials"]:
                errors = cls.MergeMAssetMaterials(a, **kwargs)
                if errors:
                    if not core.SCENE.GetSuppressWindowState():
                        errorString = ""
                        for m in errors:
                            errorString += "\n" + m
                        pCore.PopupError(errorString)

            if kwargs["uniqueNames"]:
                a.EnsureUniqueShortNames(testForUnique=True)

        MAsset_OptimiseUnused()
        newNodes = cls.RemoveUnwantedNodesFromImport(newNodes)
        if kwargs["deleteUnusedShaders"]:
            pCore.evalDeferred(pCore.mel.MLdeleteUnused)

        return roots, Assets, list(newNodes)

    @classmethod
    def FindMAssetsIn(cls, Nodes):
        '''
        Given a list of node this will find the MAssets in that list
        :returns: [MAsset,]
        '''

        toReturn = []
        iterNodes = [m for m in Nodes if all([m.exists(), (m.type() == "network")])]
        for m in iterNodes:
            if metaData.IsValidMetaNode(m):
                if m.metaClass.get() == "MAsset":
                    Asset = MAsset(m)
                    if Asset.m_IsValid():
                        toReturn.append(Asset)
        return toReturn

    @classmethod
    def UpdateAll(cls, **kw):
        '''
        Updates all MAssets in the Scene
        '''
        assetIdDict = {}
        for Asset in cls.GetAllMAssets():
            if assetIdDict.has_key(str(Asset.id)):
                assetIdDict[str(Asset.id)].append(Asset)
            else:
                assetIdDict[str(Asset.id)] = [Asset]

        for k in sorted(assetIdDict.keys()):
            AssetObj = cls.GetDataBaseAssetObject(int(k))
            cls.UpdateAssets(assetIdDict[k], AssetObj, **kw)

    @classmethod
    def ReplaceSelectedWith(cls, AssetObj, **kw):
        '''
        Replaces all the selected transforms with the given Asset
        :param AssetObj: `Asset`
        '''
        transforms = [t for t in pCore.selected() if "transform" in t.type(i=True)]
        kw.setdefault("mergeAllFileNodes", True)
        mergeAllFileNodes = kw.pop("mergeAllFileNodes")
        cls.UpdateAssets(transforms, AssetObj, **kw)
        if mergeAllFileNodes:
            tdtools.core.materials.MergeAllFileNodes(deleteUnused=False)

    @classmethod
    def ReplaceSelectedWithFilePath(cls, AssetObj, **kw):
        '''
        Replaces all the selected transforms with the given Asset
        :param AssetObj: `Asset`
        '''
        transforms = [t for t in pCore.selected() if "transform" in t.type(i=True)]
        kw.setdefault("mergeAllFileNodes", True)
        mergeAllFileNodes = kw.pop("mergeAllFileNodes")
        cls.UpdateAssets(transforms, AssetObj, **kw)
        if mergeAllFileNodes:
            tdtools.core.materials.MergeAllFileNodes(deleteUnused=False)

    @classmethod
    def SnapAsset(cls, A, B):
        '''
        Method run to align on Asset to another.
        :param A: `str` transform
        :param B: `str` transform
        '''
        pCore.mel.GingerSnapSelWrap(B, A, 4)

    @classmethod
    def UpdateAssets(cls, mAssetList, assetObj, maintainName=True, forceMaintainName=False, **kw):
        '''
        This is the "MAIN and ONLY" call that swaps one MAsset for another or a group of other root
        transforms.  This will also import the new asset from the assetObj.

        :param mAssetList: list of transforms or MAssets
        :param assetObj: Asset object form clr module
        :param maintainName: bool
        :param forceMaintainName: bool

        :keyword deleteUnusedShaders: bool
        :keyword mergeMaterials: bool
        :keyword mergeByDefinition: bool
        :keyword mergeByName: bool
        :keyword mergeUseSource: bool
        '''

        levelCache = pCore._internal.factories._logger.level
        pCore._internal.factories._logger.setLevel(50)

        _logger.info("importing asset : %s" % assetObj)
        _logger.info("options MaintainName : %s, ForceName : %s" % (maintainName, forceMaintainName))

        kw.setdefault("deleteUnusedShaders", MASSET_OPT_VARS.deleteUnusedShaders)
        kw.setdefault("mergeMaterials", MASSET_OPT_VARS.mergeMaterials)
        kw.setdefault("mergeByDefinition", MASSET_OPT_VARS.mergeMaterialsByDefinition)
        kw.setdefault("mergeByName", MASSET_OPT_VARS.mergeMaterialsByName)
        kw.setdefault("mergeUseSource", MASSET_OPT_VARS.mergeMaterialsUseSource)

        dupCount = len(mAssetList)  # no. assets in the list we need to replace
        dupAssets = []

        _logger.info("number of assets to replace : %s" % dupCount)

        assert type(mAssetList) == list
        if not mAssetList:
            return

        # this is the new asset imported from the Db
        if not isinstance(assetObj, basestring):
            newAssets_Cache, _ = cls.ImportAssetFromAssetDb(assetObj, **kw)
        else:
            newAssets_Cache, _ = cls.ImportAssetFromFilePath(assetObj, **kw)

        # @DecoratorLib.timeit
        def duplicateImportedAssets(Assets):
            '''
            This duplicates the imported assets, it's more reliable to turn off the
            select root and duplicate callbacks during the import replace and set them
            back
            '''
            state = _CALLBACK_MANAGER.getMAssetDuplicateState()

            # By forcing this to false we are going to use the Optimised Duplicate hand crafted in the MAsset.DuplicateAsset()
            # method
            _CALLBACK_MANAGER.setMAssetDuplicateEnabled(False)
            res = []

            if Assets:
                import mQt.core as ui
                with ui.MayaProgressBarManager(len(Assets), IsInterruptable=False) as pBar:
                    pBar.setText("Duplicating Assets")
                    for i, a in enumerate(Assets):
                        pBar.setValue(i + 1)
                        res.append(a.DuplicateAsset())

            _CALLBACK_MANAGER.setMAssetDuplicateEnabled(state)

            return res

        def GetRootTransform(Asset):
            '''
            If the Assets is a MAsset this will return the Root, otherwise it maybe a disolved asset or
            a standard maya transform.  For that case we just return the original input
            '''
            if isinstance(Asset, MAsset):
                try:
                    return Asset.GetRootTransform()
                except StandardError, Err:
                    _logger.exception(Err)
                    return Asset
            else:
                return Asset

        def DeleteAsset(Asset):
            '''
            When deleting Assets we don't know if they are standard MAssets or standard maya types.  So
            we have to cater for both.
            '''
            if isinstance(Asset, MAsset):
                try:
                    return Asset.Delete()
                except StandardError, Err:
                    _logger.exception(Err)
            else:
                AssetNode = MAsset_GetMAssetFrom(Asset)
                if AssetNode:
                    MAsset_ = MAsset(AssetNode)
                    MAsset_.Delete()
                else:
                    try:
                        return pCore.delete(Asset)
                    except StandardError, Err:
                        _logger.exception(Err)

        def GetOldAssetId(Asset):
            try:
                if isinstance(Asset, MAsset):
                    return Asset.id
                else:
                    AssetMetaNode = MAsset_GetMAssetFrom(Asset)
                    if AssetMetaNode:
                        Asset = MAsset(AssetMetaNode)
                        return Asset.id
                    else:
                        return -1
            except StandardError, Err:
                _logger.exception(Err)

        for i in range(0, dupCount):
            if i == 0:
                # if we're only replacing 1 Asset then the imported on will be used
                dupAssets.append(newAssets_Cache)
            else:
                # we'll loop and duplicate the Asset so we have 1 for each
                # asset we need to replace
                # because duplicateImportedAssets returns a list then
                # dupAssets will be a [[MAsset], [MAsset]]
                dupAssets.append(duplicateImportedAssets(newAssets_Cache))

        _logger.info(dupAssets)
        res = []
        for i, dupGroup in enumerate(dupAssets):
            for newAsset in dupGroup:
                rootTransform = newAsset.GetRootTransform()
                res.append(newAsset)
                if rootTransform:
                    oldAssetTransform = GetRootTransform(mAssetList[i])

                    oldID = GetOldAssetId(mAssetList[i])
                    newId = newAsset.id

                    __maintainName = False
                    if maintainName:
                        if newId == oldID:
                            __maintainName = True
                        else:
                            if forceMaintainName:
                                __maintainName = True

                    # Maintain all the data that users would want to keep
                    # IE Layer Assignments and sets etc.  Realistically we can only do this for
                    # the RootTransforms as this is the Entry point, for example the 2 structures
                    # could be different.  Education of users on this point might be needed.  Or
                    # a generic method to copy that data in complex situations.  But this would
                    # slow down the update process.  So far this hasn't been requested.
                    ParentOfAsset = oldAssetTransform.getParent()
                    LayersOfAsset = oldAssetTransform.drawOverride.inputs(type="displayLayer")
                    SetsOfAsset = oldAssetTransform.outputs(type="objectSet")
                    if oldAssetTransform:
                        _logger.debug("snapping MAsset :: %s to %s" % (rootTransform, oldAssetTransform))

                        # maintain the layer assignments
                        for l in LayersOfAsset:
                            l.drawInfo >> rootTransform.drawOverride

                        for set_ in SetsOfAsset:
                            try:
                                set_.add(rootTransform)
                            except:
                                pass
                                # Snap the Asset to the old Asset
                                # Any rotation logic may need to go here. Alternatively users should not freeze transforms
                        cls.SnapAsset(rootTransform, oldAssetTransform)
                        newName = oldAssetTransform.name()

                        _logger.info("Old Asset RootTransform Name : %s" % newName)

                        # Now we put the Asset under the right parent and maintain it's position
                        if ParentOfAsset:
                            relatives = ParentOfAsset.listRelatives()

                            # Store the current index in the list so we can maintain it
                            # and thus maintain the outliner position.  The only way I can do this is by
                            # listRelatives???!!.... Could be buggy...
                            moveAmount = None
                            try:
                                rowIndex = relatives.index(oldAssetTransform)
                                tableLength = len(relatives)
                                moveAmount = (tableLength - rowIndex) * -1
                            except StandardError, Err:
                                moveAmount = None
                                _logger.warning("Problem trying to get sceneGraph table index for reorder command")
                                _logger.exception(Err)

                            rootTransform.setParent(ParentOfAsset)

                            # now move the new root Transform to the correct position in the outliner
                            # expects the above parent command to have put the item at the foot of the table
                            # which is what it seems to do.  IE a new row.
                            if moveAmount is not None:
                                try:
                                    pCore.reorder(rootTransform, r=moveAmount)
                                    _logger.info("reordered the outliner to maintain position")
                                except StandardError, Err:
                                    _logger.warning(
                                        "Problem trying to maintain the outliner position of %s" % oldAssetTransform)
                                    _logger.exception(Err)

                        _logger.info("New Asset RootTransform Name : %s" % rootTransform.name())

                        DeleteAsset(mAssetList[i])

                        if __maintainName:
                            _logger.info("Renaming RootTransform : %s to : %s" % (rootTransform.name(), newName))
                            newAsset.SetName(newName)

        pCore._internal.factories._logger.setLevel(levelCache)
        return res


class MAsset(metaData.MetaData):
    '''
    A MAsset is a MetaNode that is wrapped by this class to provide methods that will enable
    an Asset(should be Assets from Maya but they are to buggy) like mentality.


     ------------         -----[X] RootTransform (Special AssetMember)
    |   MAsset   |_______|
    | (metaNode) |       |
     ------------         -----[X] AssetMember

    MAssets must have a single RootTransform.  If more that 1 AssetMember is set then we
    look for the rootOf the Members to find the RootTransform.

    MAsset MetaData nodes are given an UUID at creation time.  Members are also tagged with
    this UUID so that if the connections are deleted from the MAsset, we should be able to recreate
    an MAsset.

    TODO: Drag and Drop in the Outliner
          -----------------------------

          * Should MAssets be allowed to be parented under another MAsset?
          * If So, should it be only if it's the RootTransfrom
          * If it's not the RootTransform then should we automatically remove the member and
            add it to the Asset in the outliner?

         BlackBox or Similar
         -------------------

         * Can we use itemFilter to work on MAssets with blackBox = True checkBox attribute
           to give us a similar workflow to standard Assets

        BlackBox Viewport Selection Mode
        --------------------------------

        * If we can do BlackBox in the outliner can we go further and lock the selection of
          NonRootMembers in the modelPanels.  We someone selects a NonRootTransform then
          the RootTransform is selected instead.  ZooTrigger does something like this.  But
          how fast is it? What happens with multiple object selections?  Can you install
          an itemFilter to the modelPanels to do this instead?
    '''

    def __init__(self, Node=None, Name="", Selection=False, **kw):
        if Node:
            super(MAsset, self).__init__(Node, **kw)
            self._SetInitialProperties()
            self.AutoSetRoot()
        else:
            super(MAsset, self).__init__(Node, **kw)
            self._SetInitialProperties()
            if Selection:
                self.AddAssetMembers(pCore.selected())
            self.AutoSetRoot()
            self.SetName(Name)
            # _MAssetDagMenu.serialize(self.MetaNode)

    def __ModificationDate(self, filename):
        t = pCore.util.path(filename).getmtime()
        return datetime.datetime.fromtimestamp(t)

    def RefreshUUID(self):
        '''
        Genereates a new UUID and stamps the data on all Members
        '''
        self.UUID = str(uuid.uuid4())
        for _ in self.GetAssetMembers():
            root = self.GetRootTransform()
            self.AddAssetMembers(self.GetAssetMembers())
            self.SetRootTransform(root)

    def _SetInitialProperties(self):
        self.m_SetInitialProperty("UUID", str(uuid.uuid4()), "LOCKED")

    def EnsureUniqueShortNames(self, members=[], testForUnique=False):
        _logger.debug("EnsureUniqueShortNames")
        if not members:
            members = self.GetAssetMembers()
        for node in members:
            if node.lodVisibility.inputs():
                continue

            shapes = node.getShapes()

            nodeName = pCore.other.NameParser(node.split("|")[-1])
            doIt = False
            if testForUnique:
                if len(pCore.cmds.ls(nodeName)) > 1:
                    doIt = True
                else:
                    for shape in shapes:
                        shapeName = pCore.other.NameParser(shape.split("|")[-1])
                        if len(pCore.cmds.ls(shapeName)) > 1:
                            doIt = True
            else:
                doIt = True

            if doIt:
                nodeName = nodeName.nextUniqueName()
                node.rename(nodeName)
                for shape in shapes:
                    nameNoNumber = nodeName.stripNum()
                    try:
                        number = int(nodeName.lstrip(nameNoNumber))
                        shape.rename("{0}Shape{1}".format(nameNoNumber, number))
                    except:
                        pass

    def GetLODMembers(self, sortByPlug=True):
        """
        Returns the tagged members that are controled by lodGroups and the plug that controls them
        :return: [(nt.Transform, nt.Attribute(*.output[0])), ]
        """
        res = []
        sortedPlugs = []
        for m in self.GetAssetMembers():
            plugs = m.lodVisibility.inputs(plugs=True)
            if plugs:
                sortedPlugs.append(plugs[0])

        sortedPlugs.sort()
        for plug in sortedPlugs:
            transform = plug.outputs()[0]
            res.append((transform, plug))
        return res

    def GetAssetMembers(self):
        return self.m_GetTagged()

    def GetNonRootMembers(self):
        return list(set(self.GetAssetMembers()) - set([self.GetRootTransform()]))

    def GetInstances(self):
        """
        As you can instance a MAsset this function returns the other instances of the MAsset
        :return:
        """

        def getPartData(node):
            try:
                return node.MAsset_Part.get()
            except:
                return ""

        res = []
        for m in self.GetAssetMembers():
            if m.isInstanced():
                others = m.getOtherInstances()
                for node in others:
                    walk = True
                    count = 0
                    while walk:
                        if not node:
                            walk = False
                        if count > 20:
                            walk = False
                        data = getPartData(node)
                        if '"Root": true' in data:
                            res.append(node)
                            walk = False
                        else:
                            node = node.getParent()
                break
        return res

    def AddAssetMembers(self, Node):
        if getattr(Node, "__iter__", None):
            for n in Node:
                if n.type() in ["transform", "assemblyDefinition"]:
                    if n.getShape():
                        if n.getShape().type() in ["mesh", "gpuCache"]:
                            md = self.m_GetTaggedWith(n, self.__class__.__name__, AsMetaData=False)
                            for m in md:
                                if m != self.MetaNode:
                                    raise StandardError("The node :: %s is already a member of another MAsset" % n)
                            self.m_SetAsPart(n, {"Root": False, "UUID": self.UUID})

                            try:
                                n.translate.setLocked(True)
                                n.rotate.setLocked(True)
                                n.scale.setLocked(True)
                                shapes = n.getShapes()
                                for shape in shapes:
                                    try:
                                        shape.allowTopologyMod.set(False)
                                    except AttributeError, Err:
                                        pass
                                self.SetLockTransformPivot(n, True)
                            except StandardError, Err:
                                _logger.exception(Err)

                                # _MAssetDagMenu.setChildNode(n)
        else:
            self.m_SetAsPart(Node, {"Root": False, "UUID": self.UUID})
            Node = pCore.PyNode(Node)
            if Node.type() in ["transform", "assemblyDefinition"]:
                if Node.getShape().type() in ["mesh", "gpuCache"]:
                    try:
                        Node.translate.setLocked(True)
                        Node.rotate.setLocked(True)
                        Node.scale.setLocked(True)
                        shapes = Node.getShapes()
                        for shape in shapes:
                            try:
                                shape.allowTopologyMod.set(False)
                            except AttributeError, Err:
                                pass
                        self.SetLockTransformPivot(Node, True)
                    except StandardError, Err:
                        _logger.exception(Err)

                        # _MAssetDagMenu.setChildNode(Node)

    def GetCollisionMembers(self):
        '''
        Generic procedure that looks at all the asset members and returns the members that last
        part of the name == "COL" | "COLLISION" or is attached to a layer who's name matches "COL" | "COLLISION"
        :return: [PyNode,]
        '''
        searchList = ["COL", "COLLISION"]
        return self.__SearchForPostFix(searchList)

    def GetPlayerCollisionMembers(self):
        '''
        Generic procedure that looks at all the asset members and returns the members that last
        part of the name == "PLR" | "PLAYER" or is attached to a layer who's name matches "PLR" | "PLAYER"
        :return: [PyNode,]
        '''
        searchList = ["PLR", "PLAYER"]
        return self.__SearchForPostFix(searchList)

    def GetBulletCollisionMembers(self):
        '''
        Generic procedure that looks at all the asset members and returns the members that last
        part of the name == "BUL" | "BULLET" or is attached to a layer who's name matches "BUL" | "BULLET"
        :return: [PyNode,]
        '''
        searchList = ["BUL", "BULLET"]
        return self.__SearchForPostFix(searchList)

    def GetAllCollisionMembers(self):
        '''
        All the collision members
        :return: [PyNode,]
        '''
        res = self.GetCollisionMembers()
        res.extend(self.GetBulletCollisionMembers())
        res.extend(self.GetPlayerCollisionMembers())
        return res

    def __SearchForPostFix(self, searchList):
        '''
        For all the members this will search for a postFix on the obj or layer that matches any of the
        given list of strings
        :param searchList: [`str`,]
        :return: [PyNode,]
        '''

        def getSearchName(node):
            return node.stripNum().upper().split("_")[-1]

        res = []
        for m in self.GetAssetMembers():
            searchName = getSearchName(m)
            if searchName in searchList:
                res.append(m)
            else:
                attr = getattr(m, "drawOverride", None)
                if attr:
                    layers = attr.inputs(type="displayLayer")
                    for l in layers:
                        searchName = getSearchName(l)
                        if searchName in searchList:
                            res.append(m)
        return res

    def GetAssetTimeStamp(self):
        '''
        Converts the current ModifiedDate attribute to a datetime.  This attribute is
        stamped onto the asset when it's imported and can be used to know if the asset needs
        to be updated.

        :return: `datetime.datetime`
        '''
        timestamp = getattr(self, "ModifiedDate", None)
        if timestamp:
            args = tuple(timestamp)
            return datetime.datetime(*args)

    def GetPathModifiedDate(self):
        if self.fullPath:
            return self.__ModificationDate(self.fullPath)

    def IsOutOfDate(self):
        '''
        Checks the `GetModifiedDate` of the asset and compairs with the Asset.path modified
        time to check if the Asset is older than the file.  If it is the True will be returned

        :return: bool
        '''
        path_ = pCore.util.path(self.fullPath)
        if path_.exists():
            fileMTime = self.__ModificationDate(path_)
            assetMTime = self.GetAssetTimeStamp()
            if fileMTime > assetMTime:
                return True
        return False

    def GetAssetShadingGroups(self):
        sgs = []
        for n in self.m_GetTagged():
            if n.type() == "transform":
                shapes = n.getShapes()
                if shapes:
                    for s in shapes:
                        shadingEngines = s.outputs(type="shadingEngine")
                        if shadingEngines:
                            sgs.append(set(shadingEngines))
        unionGroup = set()
        for set_ in sgs:
            unionGroup.update(set_)
        return list(unionGroup)

    def GetMaterials(self):
        shadingGroups = self.GetAssetShadingGroups()
        _logger.debug("GetMaterials : ShadingGroups > %s" % pformat(shadingGroups))

        defaultNodes = ["lambert1", "initialShadingGroup"]

        def GetMaterialFromShadingEngine(shadingEngine):
            materials = pCore.cmds.listConnections("%s.surfaceShader" % shadingEngine)
            if materials:
                if materials[0] not in defaultNodes:
                    return pCore.PyNode(materials[0])
        mats = set()
        for sg in shadingGroups:
            m = GetMaterialFromShadingEngine(sg)
            if m:
                mats.add(m)
        return mats

    def SetRootTransform(self, Node):
        Node = pCore.PyNode(Node)
        currentTransform = self.GetRootTransform()
        if currentTransform:
            self.m_RemovePart(currentTransform, deleteConnection=True)
            currentTransform.translate.setLocked(False)
            currentTransform.rotate.setLocked(False)
            currentTransform.scale.setLocked(False)
        self.m_SetAsPart(Node, {"Root": True, "UUID": self.UUID})

        for n in self.GetNonRootMembers():
            if not n.longName().startswith(Node.longName()):
                self.m_RemovePart(n, deleteConnection=True)
        try:
            Node.translate.setLocked(False)
            Node.rotate.setLocked(False)
            Node.scale.setLocked(True)
            self.SetLockedRootPivots(True)
        except StandardError, Err:
            _logger.exception(Err)

    def SetLockedRootPivots(self, State):
        currentTransform = self.GetRootTransform()
        if currentTransform:
            self.SetLockTransformPivot(currentTransform, State)

    def SetLockedNonRootPivots(self, State):
        for t in self.GetNonRootMembers():
            self.SetLockTransformPivot(t, State)

    def SetLockTransformPivot(self, Trans, State):
        Trans = pCore.PyNode(Trans)
        assert Trans.type() in ["transform", "lodGroup", "assemblyDefinition"]
        channels = ["x", "y", "z"]
        attrs = ["rp", "rpt", "sp", "spt", "ra", "rq"]
        for c in channels:
            for at in attrs:
                plug = getattr(Trans, at + c)
                plug.setLocked(False)  # nasty hack as the lock isnt working on duplicated assets - SK
                plug.setLocked(State)

    def IsRootLocked(self):
        currentTransform = self.GetRootTransform()
        if currentTransform:
            channels = ["x", "y", "z"]
            attrs = ["rp", "rpt", "sp", "spt", "ra", "rq"]
            for c in channels:
                for at in attrs:
                    plug = getattr(currentTransform, at + c)
                    if not plug.isLocked():
                        return False
        return False

    def GetRootTransform(self):
        for n, d in self.m_GetParts():
            if d.has_key("Root"):
                if d["Root"]:
                    return n

    def SetRootTransformPivot(self, pivot, **kwargs):
        root = self.GetRootTransform()
        self.SetLockedRootPivots(False)
        root.setPivots(pivot, **kwargs)
        self.SetLockedRootPivots(True)

    def AutoSetRoot(self):
        '''
        If there is no tagged RootTransform then we look for the root from the
        contents of the MAsset.  See `AddAssetMembers` and `SetRootTransform`
        '''
        if not self.GetRootTransform():
            roots = set()
            contents = self.GetAssetMembers()
            for a in contents:
                roots.add(a.root())
            if len(roots) == 1:
                self.SetRootTransform(list(roots)[0])
            else:
                if contents:
                    sceneName = pCore.sceneName()
                    if sceneName:
                        try:
                            sceneName, _ = sceneName.basename().split(".")
                        except ValueError:
                            sceneName = contents[0].name()

                    # meshes = set([m for m in contents if m.getShape() == "mesh"])
                    # root = pCore.group(meshes, n=sceneName)
                    root = pCore.group(roots, n=sceneName)
                    self.SetRootTransform(root)

    def SetName(self, Name="", PrefixName=True):
        '''
        Sets the self.MetaNode.Name() and self._MetaNodeName, Also set the RootTransform
        name
        '''
        root = self.GetRootTransform()
        ns = ""
        if root:
            ns = root.namespace()
            if not Name:
                Name = root.nodeName()
        super(MAsset, self).m_SetName("%s%s" % (ns, Name), PrefixName)
        if root:
            root.rename("%s%s" % (ns, Name))

    def setAssetDataDict(self, data):
        for key in sorted(data):
            d = data[key]
            setattr(self, key, d)
            self.m_RegisterLockedAttr(key)

        reprDate = repr(self.__ModificationDate(data["assetPath"]))
        dateList = [int(i) for i in reprDate.strip("datetime.datetime")[1:-1].split(",")]
        self.ModifiedDate = dateList
        self.m_RegisterLockedAttr("ModifiedDate")

    def SetAssetDbObj(self, AssetDbObj):
        '''
        Stamps the AssetDb information onto the MAsset MetaNode
        '''
        import tdtools.assetSpider.astDb as astDb
        Add_Dict = astDb.AssetDbHelper.assetToStampDictionary(AssetDbObj)
        for key in sorted(Add_Dict):
            data = Add_Dict[key]
            setattr(self, key, data)
            self.m_RegisterLockedAttr(key)
            self.m_SerializePropertyForExport(key, key, False)

        reprDate = repr(self.__ModificationDate(AssetDbObj.getResolvedPath()))
        dateList = [int(i) for i in reprDate.strip("datetime.datetime")[1:-1].split(",")]
        self.ModifiedDate = dateList
        self.m_RegisterLockedAttr("ModifiedDate")

    def GetAssetDbObj(self):
        if getattr(self, "Id", None):
            AssetDbObj = MAssetUtils.GetDataBaseAssetObject(self.id)
            if not AssetDbObj:
                raise StandardError("Could not find Asset from Id : {0}".format(self.id))
            return AssetDbObj
        else:
            raise AttributeError("MAsset : {} has no attribute Id, could not determine Asset DB object without Id")

    @classmethod
    def IsAssetMember(cls, Node):
        '''
        :returns: `bool`
        '''
        return bool(cls.m_GetMetaData(Node, False, MetaDataType=cls.__name__))

    @classmethod
    def IsRootTransform(cls, Node):
        '''
        :returns: `bool`
        '''
        Node = pCore.PyNode(Node)
        if cls.IsAssetMember(Node):
            Asset = cls.GetMAsset(Node)
            return Asset.GetRootTransform() == Node

    @classmethod
    def GetMAsset(cls, Node, AsMetaData=True):
        '''
        :param Ndoe: `str` or PyNode
        :param AsMetaData: `bool`
        :returns: `MAsset` from the Node
        '''
        if cls.IsAssetMember(Node):
            return cls.m_GetMetaData(Node, AsMetaData, MetaDataType=cls.__name__)[0]

    def DuplicateAsset(self):
        '''
        Makes a completely new MAsset
        :returns: `MAsset`
        '''

        # If the duplicate callback is running then we don't do any of this any
        # longer we just duplicate away...

        if _CALLBACK_MANAGER.getMAssetDuplicateState():
            pCore.select(self.GetRootTransform())

            pCore.duplicate(rr=True)
            dup = pCore.selected()
            mNode = MAsset_GetMAssetFrom(dup[0].name())
            return MAsset(mNode)
        else:
            # If not then this is the logic needed to make a new MAsset
            # This is the default logic run when assets are imported and duplicated as
            # the callback seems to run intermittently during imports.
            NewAsset = None
            Members = self.GetAssetMembers()
            Root = self.GetRootTransform()

            if not Members:
                raise StandardError("Can't duplicate an MAsset that has no Members")
            if not Root:
                raise StandardError("Illegal MAsset, Must have a Root Transform")

            NewName = ""
            MembersShortNames = [m.shortName().split("|")[-1] for m in Members]
            oldLodMembers = self.GetLODMembers()
            oldLodMeshes = [m[0].shortName().split("|")[-1] for m in oldLodMembers]
            oldPlugs = [m[1] for m in oldLodMembers]

            currentNameSpaceOfAsset = self.MetaNode.namespace()
            currentNameSpace = pCore.namespaceInfo(cur=True)
            if not currentNameSpaceOfAsset.startswith(":"):
                currentNameSpaceOfAsset = ":" + currentNameSpaceOfAsset
            if not currentNameSpace.startswith(":"):
                currentNameSpace = ":" + currentNameSpace

            try:
                # This needs more testing as containers aren't being used
                if Root.type() == 'dagContainer':
                    newDagContainer = pCore.duplicate(Root, rr=True, rc=True, ic=True)[0]
                    members = pCore.container(newDagContainer, q=True, nodeList=True)
                    if members:
                        for m in members:
                            mData = MAsset.m_GetMetaData(m, MetaDataType='MAsset')
                            if mData:
                                return mData[0]
                    return
                else:
                    NewName = Root.name()

                pCore.namespace(set=currentNameSpaceOfAsset)

                NewAssetMembers = pCore.duplicate(Root, rr=True)
                NewAssetMembers += [pCore.PyNode(m) for m in NewAssetMembers[0].listRelatives(ad=True, type="transform") \
                                    if m.shortName().split("|")[-1] in MembersShortNames]

                # We can't use duplicate for a metaNode because the message links are retained
                NewAsset = MAsset(Name=NewName)
                self.CopyMAssetDbAttrs(NewAsset)

                rootTrans = None
                lod = None
                for m in NewAssetMembers:
                    if not lod:
                        if m.type() == "lodGroup":
                            lod = m
                            camera = pCore.mel.findStartUpCamera("persp")
                            if camera:
                                camera = pCore.PyNode(camera)
                                camera.worldMatrix >> m.cameraMatrix

                    d = self.m_GetPartData(m, BypassIsPart=True)
                    if d.has_key("Root"):
                        if d["Root"]:
                            rootTrans = m
                if lod:
                    for m in NewAssetMembers:
                        if m.type() != "lodGroup":
                            try:
                                shortName = m.shortName().split("|")[-1]
                                index = oldLodMeshes.index(shortName)
                                plug = pCore.PyNode("%s.%s" % (lod, oldPlugs[index].name(includeNode=False)))
                                plug >> m.lodVisibility
                            except ValueError:
                                continue

                NewAsset.AddAssetMembers(NewAssetMembers)
                if rootTrans:
                    NewAsset.SetRootTransform(rootTrans)
                NewAsset.EnsureUniqueShortNames(NewAssetMembers)

            except StandardError, Err:
                _logger.exception(Err)
            pCore.namespace(set=currentNameSpace)

            return NewAsset

    def CopyMAssetDbAttrs(self, NewAsset):
        '''
        Copies all the AssetDb Attributes from this MAsset to the new MAsset
        :param NewAsset: MAsset
        :return: None
        '''
        filterAttrs = ["nodeState", "metaClass", "metaVersion", "UUID", "rmbCommand", "selectCommand",
                       "BlackBox", "metaNetwork", "metaTagged"]
        copyAttrs = [a.longName() for a in self.m_GetMetaNodeAttributes() if a.longName() not in filterAttrs]
        for attr in copyAttrs:
            setattr(NewAsset, attr, getattr(self, attr, ""))
            pnAttr = getattr(NewAsset.MetaNode, attr, None)
            if pnAttr:
                try:
                    pnAttr.setLocked(True)
                except StandardError as e:
                    pass

    @classmethod
    def DuplicateParts(cls, Nodes):
        '''
        DuplicateParts is for duplicating a AssetMember that isn't the RootTransform.
        Hooks the new object up to the MAsset
        '''
        res = []
        if not isinstance(Nodes, list):
            Nodes = [Nodes]
        else:
            Nodes = [pCore.PyNode(n) for n in Nodes if n]
        for n in Nodes:
            if cls.IsAssetMember(n):
                Asset = cls.GetMAsset(n)
                if Asset.GetRootTransform() == n:
                    pass
                else:
                    newNode = pCore.duplicate(n, rr=True, rc=True)
                    res.append(newNode)
                    Asset.AddAssetMembers(newNode)
        return res

    def Dissolve(self, deleteSelf=True):
        '''
        Removes all the MAsset links and enables editing on the Asset
        :return: `bool`  success status
        '''
        with pCore.UndoChunk():
            try:
                for member in self.GetAssetMembers():
                    if member.type() == "transform":
                        member.translate.setLocked(False)
                        member.rotate.setLocked(False)
                        member.scale.setLocked(False)
                        for shape in member.getShapes():
                            shape.allowTopologyMod.set(True)
                        try:
                            self.m_RemovePart(member, deleteConnection=True)
                        except:
                            pass
                        try:
                            member.setLocked(False)
                            self.SetLockTransformPivot(member, False)
                        except:
                            pass
                            # _MAssetDagMenu.removeChildNode(member)
                if deleteSelf:
                    super(MAsset, self).m_Delete()

                return True
            except StandardError, Err:
                _logger.exception(Err)
                return False

    def PushEditsBackToSource(self):
        supportedExtensions = [".ma", ".mb"]
        mappedExtensions = ["mayaAscii", "mayaBinary"]
        outExt = ""

        root = self.GetRootTransform()
        if root:
            if len(self.GetAssetMembers()) > 1:
                '''
                Children of the MAsset Root are locked preventing freezing the geometry
                So we can "assume" that we can reset the Asset and Export it over the original
                '''
                DBAsset = MAssetUtils.GetDataBaseAssetObject(self.id)
                if not DBAsset:
                    raise StandardError("Asset with ID:{0} not found in the DataBase".format(self.id))

                origPath = tdtools.core.fileTools.EFile(DBAsset.path)
                if origPath.exists():
                    if not origPath.IsLocked:
                        ext = origPath.ext.lower()
                        if ext in supportedExtensions:
                            outExt = mappedExtensions[supportedExtensions.index(ext)]
                        else:
                            _logger.warning("Only .ma and .mb files are supported!")
                            return

                        copy = self.DuplicateAsset()
                        try:
                            root.setParent(None)
                            root.translate.set([0, 0, 0])
                            root.rotate.set([0, 0, 0])
                            pCore.select(root)
                            self.Dissolve()
                            pCore.exportSelected(origPath, f=True, type=outExt)
                            self.Delete()
                        except StandardError, Err:
                            _logger.exception(Err)
                            self.Delete()
                            raise Err
                    else:
                        _logger.warning("MAsset Source Path is Locked, Check the file out please")
            else:
                _logger.warning("MAsset has only 1 Root.  It's not safe to assume the Asset hasn't been frozen")

    def m_IsValid(self):
        return bool(self.GetRootTransform())

    def m_Delete(self, *args, **kw):
        self.Dissolve(deleteSelf=True)

    def Delete(self, doBasicOptimise=False):
        '''
        Completely deletes all to asset members and MAssetNode MetaNode.

        TODO: Implement __del__ as a cleaner way to deal with the instance
        '''
        pCoreLogLevel = pCore.nt._logger.level
        pCore.nt._logger.setLevel(50)
        members = [n.longName() for n in self.GetNonRootMembers()]
        root = self.GetRootTransform()
        self.Dissolve()
        try:
            pCore.delete(root)
        except:
            pass
            # No the children and the metaNode are potentialy gone,
        # but we need to try to clean them anyway
        members = [n for n in members if pCore.objExists(n)]
        members += [self.MetaNode]
        for n in members:
            try:
                pCore.delete(n)
            except:
                pass
        pCore.nt._logger.setLevel(pCoreLogLevel)

        if doBasicOptimise:
            # We have to stop the pop up window.  Must be a cleaner may to this
            _logger("MAsset.Delete() is doing optimise...")
            cmd = '''putenv "MAYA_TESTING_CLEANUP"  "DontShow";'''
            pCore.mel.eval(cmd)
            pCore.mel.OptimizeScene()

# ======================================================================================
#
# All commands that need wrapping should be added below!
#
# ======================================================================================


global MEL_WRAP_FUNCTIONS
MEL_WRAP_FUNCTIONS = [(MAsset_Rmb_Duplicate, ['string'], None),
                      (MAsset_GetMAssetFrom, ['string'], 'string'),
                      (MAsset_GetNonRootMembers, ['string'], 'string[]'),
                      (MAsset_GetRootTransform, ['string'], 'string'),
                      (MAsset_Rmb_UpdateAsset, ['string'], None),
                      (MAsset_Rmb_SelectAllRootTransformsById, ['string'], None),
                      (MAsset_OptimiseUnused, [None], None),
                      (MAsset_Rmb_OpenSource, ['string'], None),
                      (MAsset_Rmb_SelectAssetMembers, ['string'], None),
                      (MAsset_Rmb_SelectMAsset, ['string'], None),
                      (MAsset_Rmb_SelectNonRootMembers, ['string'], None),
                      (MAsset_Rmb_SelectRootTransform, ['string'], None),
                      (MAsset_Rmb_Dissolve, ['string'], None),
                      (MAsset_FilterRootTransform, ['string'], 'int'),
                      (MAsset_FilterNonRootTransform, ['string'], 'int'),
                      (MAsset_FilterArray_RootTransform, ['string'], 'string[]'),
                      (MAsset_ToggleFilterOutliner, [None], None),
                      (MAssetGlobalOptionsDialog, [None], None),
                      (MAsset_Rmb_UpdateAllUnderMouseById, ['string'], None),
                      (MAsset_Dissolve_Selected, [None], None),
                      (MAsset_PushChangesBackToSource_Selected, [None], None)]


def RegisterMAssetFunctions(force=False):
    Install_FilterArray_RootTransform_MelProcedure()
    try:
        import tdtools.core.general as _gen
        for f, args, retType in MEL_WRAP_FUNCTIONS:
            _gen.MelFunctioner(f, args, retType).Register(force=True)
    except ImportError as e:
        pass

# Register the functions on import.  Only does the ones that arn't already defined
RegisterMAssetFunctions()
