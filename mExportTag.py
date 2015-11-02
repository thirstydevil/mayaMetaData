"""
**eMExportTag** is a module that via metaNode's in the Maya scene can return Data about
an exportTag.

This is the maiode for all the ExportTagging and management pipeline which replaces
the Mel legacy code. This also has supprot to deal with and convert the old ExportTag
to the new eMtags.

A Maya node can have only ONE exportTag assigned to it by design and no child nodes of
the given can have tags associated to them.

Example::

    #imported via the eBatchProcessorImports stub as eMTag

    #Add and exportTag to the given node or type Character.
    #Note that the type is passed in via the TAG_TYPE class
    tag=eMTag.AddExportTag(pCore.selected()[0], eMTag.TAG_TYPE.Character,'ENMY')

    #from the selected MayaNode give me back the eMExp tag object
    tag=eMTag.GetExportTagFromSelected(pCore.selected()[0])[0]

    #Remove the ExportTag
    eMTag.RemoveExportTag(pCore.selected())

    #Finding Data -------------------------------------------

    #Find all ExportTags of Type Camera - return the mTag objects
    tags=eMTag.FindAllMExportTags(TagType=eMTag.TAG_TYPE.Camera)

    #Find all exportTags in the scene and return the data as longPath string to the
    #tagged Maya rootNode itself (mel legacy support)
    tags=eMTag.FindAllMExportTags(ReturnType='LongName')

    #Overrides ----------------------------------------------

    #Add and Get the overrides which are used to add or remove child nodes of
    #the Tags RootNode from the export selection lists. Note there are 2 options
    #'Include' or 'Exclude' in all of the Override calls
    tag.AddOverRides(pCore.selected(),'Include')
    tag.GetOverRides('Include')
"""

import logging
import time
from functools import wraps

import pymel.core as pCore
import maya.cmds as cmds
import metaData as eMetaData

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def Timer(func):
    def wrap(*args, **kw):
        _logger.info("Calling... %s" % func.__name__)
        ts = time.time()
        data = func(*args, **kw)
        te = time.time()
        total = te - ts
        _logger.info('%.6f' % total)
        return data
    return wrap


def memo(func):
    cache = {}

    @wraps(func)
    def wrap(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]

    return wrap


def FindAllMExportTags(TagType=None, MayaNodes=None, AsMetaData=True, ValidOnly=True, RemoveInvalids=True):
    """
    Run through the entire scene to get any MExport Tagged Objects

    :param TagType: Only return Tags of the given type - accepts Tag as str, TAG_TYPE, OR MExportClass
    :param MayaNodes: cmds.MayaNodes to scan for Tags, cmds for speed on large datasets
    :returns: All `MExportTag` instances in the scene
    :rtype: [`MExportTags`]
    """
    Tags = []

    if MayaNodes:
        mData = pCore.cmds.listConnections(MayaNodes, d=False, s=True, type="network")
        if mData:
            mData = set(mData)
    else:
        mData = pCore.cmds.ls(type="network", l=True)

    if not mData: return []

    iterator = []

    if TagType:
        iterator = (n for n in eMetaData.IterFilterMetaNodesForClass(mData, TagType, asMetaData=False))
    else:
        iterator = (n for n in eMetaData.IterMetaNodesForBaseClass("MExportTag", asMetaData=False))

    for tag in iterator:
        if ValidOnly:
            if not cmds.listConnections('%s.metaTagged' % tag):
                if RemoveInvalids:
                    eMetaData.MetaData(tag).m_Delete()
                continue
        if AsMetaData:
            tag = eMetaData.MetaData(tag)
        Tags.append(tag)

    return Tags


def FindExportTags(TagType=None, Select=False, Active=False, SearchTags=[], ReturnType='MTags', MayaNodes=None,
                   ValidOnly=False, RemoveInvalids=True, **kwargs):
    """
    Run through the entire scene to get any ExportTagged Objects
    ..note::

    :param Type: TagTypes to return/process
    :param Select: select the results
    :param Active: only return ExportTags that are Active
    :param SearchTags: only return data for Tags that Match the given list
    :param ReturnType: Whether to return the MTags or String object data.

        * MTags = (default) eMExportTag Class
        * MTagNode = MetaNode for eMTag
        * Nodes = PyNodes of the RootNodes connected to this Tag
        * LongName = mel code requirement legacy, longName as String

    :param MayaNodes: cmds.MayaNodes to scan for Tags, cmds for speed on large data sets
    """
    SortReturn = True
    ReturnTags = []
    Tags = []
    kwargs.setdefault('InterfaceProxy', False)
    InterfaceProxy = kwargs['InterfaceProxy']

    # Ensure we're dealing with an iterable
    # This needs to be from the ENUM above

    if SearchTags and not isinstance(SearchTags, list): SearchTags = [SearchTags]

    if ReturnType == 'MTags':
        Tags = FindAllMExportTags(TagType=TagType, MayaNodes=MayaNodes, AsMetaData=True, ValidOnly=ValidOnly,
                                  RemoveInvalids=RemoveInvalids)
    else:
        Tags = FindAllMExportTags(TagType=TagType, MayaNodes=MayaNodes, AsMetaData=False, ValidOnly=ValidOnly,
                                  RemoveInvalids=RemoveInvalids)
        if Tags:
            InterfaceProxy = True

    if not Tags:
        return []

    for tag in Tags:
        if InterfaceProxy:
            # cast the metaNode into the interface Proxy which gets the
            # data directly from the node rather than the MTagClass for speed
            tag = MExportTag_InterfaceProxy(tag.MetaNode)

        if Active and not tag.TagActive:
            continue
        if SearchTags:
            # if given return only Tags that match the name inputs
            [ReturnTags.append(tag) for sTag in SearchTags if tag.TagNote == sTag]
        else:
            ReturnTags.append(tag)

    # sort the paired lists by the first value in each
    if SortReturn:
        ReturnTags = sorted(ReturnTags, key=lambda x: x.TagNote.upper())

    if Select:
        pCore.select(cl=True)
        [pCore.select(tag.rootNode(), add=True) for tag in ReturnTags]

    if ReturnType == 'MTags':
        return ReturnTags

    elif ReturnType == 'Nodes':
        return [tag.rootNode() for tag in ReturnTags]

    elif ReturnType == 'LongName':  # mel code requirement legacy
        return [tag.rootNode().longName() for tag in ReturnTags]

    elif ReturnType == 'TagNote':  # mel code requirement legacy
        return [tag.TagNote for tag in ReturnTags]
    else:
        return ReturnTags


def FindExportTagUnderHierarchy(RootNode=None, nodeTypes=None, AsMetaData=False):
    """
    Fast hierarchy search for finding MExportTags under a hierarchy. This needs linking
    into the AddExportTag call to make sure you can't nest ExportTags in future
    :param RootNode: CMDS MayaNode/Nodes
    :param nodeTypes: only test childNodes of type, simple speed up
    :param AsMetaData: return the ExportClass Object or just the Maya node
    :return Export Tagged Maya Node
    """
    returnType = 'LongName'
    if AsMetaData:
        returnType = 'MTags'
    Nodes = []
    if not RootNode:
        RootNode = pCore.selected()[0].longName()
    else:
        # we have to do this to make sure the | characters have been passed in properly.
        RootNode = pCore.PyNode(RootNode).longName()
    if nodeTypes:
        Nodes = pCore.cmds.listRelatives(RootNode, ad=True, f=True, type=nodeTypes)
    else:
        Nodes = pCore.cmds.listRelatives(RootNode, ad=True, f=True, type='transform')
    if isinstance(Nodes, list):
        Nodes.append(RootNode)
    else:
        Nodes = []
        Nodes.append(RootNode)

    def startswith(obj, name):
        if isinstance(obj, basestring):
            return obj.startswith(name)
        elif isinstance(obj, pCore.PyNode):
            return obj.longName().startswith(name)
        elif isinstance(obj, eMetaData.MetaData):
            return obj.MetaNode.startswith(name)
        else:
            raise TypeError("%s" % type(obj))

    Nodes.reverse()

    return [n for n in FindExportTags(MayaNodes=Nodes, ReturnType=returnType) if startswith(n, RootNode)]


def FindExportTagAboveHierarchy(Nodes=None, AsMetaData=False):
    """
    This is Used in the PreSelection Handler of the UI to select the relevant
    ExportTags in the UI from selected nodes in the scene.

    From a Selected MayaNode walk the parent hierarchy to find any MExportTags
    Note: there is specific handling for dealing with animRigs
    :param Nodes: CMDS MayaNode/Nodes
    :param AsMetaData: return the ExportClass Object or just the Maya node
    :return Export Tagged Maya Node
    """
    loop = 0
    tags = []
    Character = None
    selection = cmds.ls(sl=True, l=True)
    if Nodes is None:
        toProcess = cmds.ls(sl=True, l=True)
    else:
        if not getattr(Nodes, "__iter__", None):
            Nodes = [Nodes]
        toProcess = Nodes

    parents = set(toProcess)

    #Test for Characters first, this saves itterating over multiple nodes in the
    #hierarchy whilst doing the walk and doing the same test for MasterNode
    rootsTested = [] #store rootNodes of each node as thats the entry point for the MasterNode search
    for node in parents:
        if 'dagNode' in cmds.nodeType(str(node), i=True):
            Character = pCore.mel.FindMasterFromAnyNode(node)
        if Character:
            if not node.split('|')[0] in rootsTested:
                toProcess.remove(node)
                _logger.info('FindExportTagUnderHierarchy called on node : %s' % node)
                Data = FindExportTagUnderHierarchy(Character, nodeTypes='joint', AsMetaData=AsMetaData)
                if Data:
                    print "DATA", Data
                    tags.extend(Data)
                rootsTested.append(node.split('|')[0])
            else:
                _logger.debug('Skipping as Hierarchy tested for Charcater already %s' % node)

    parents = set(toProcess)

    #Not a part of a Character System so lets walk it
    if toProcess:
        while toProcess:
            if loop > 300:
                break
            if not parents:
                break

            for node in set(parents):

                #Try find the exportTag on this node first
                Data = eMetaData.MetaData.m_HasMetaData(node, MetaDataRelaxedType='MExportTag')
                if not Data:
                    Data = cmds.attributeQuery('ExportSpecific', node=node, exists=True)
                if Data:
                    if AsMetaData:
                        tags.append(GetExportTagFromSelected(pCore.PyNode(node), AsMetaData=AsMetaData)[0])
                    else:
                        tags.append(node)
                    toProcess.remove(node)
                    continue

            if toProcess:
                parents = cmds.listRelatives(toProcess, p=True, f=True)
                if parents:
                    toProcess = list(parents)
            loop += 1
    if selection:
        cmds.select(selection)
    return tags


def GetExportTagFromSelected(Nodes=None, AsMetaData=True):
    """
    From selected or given Maya Nodes return all linked ExportTags as MExportTags
    This is backward compatible, all old Tags will return an MExport_Proxy object
    :param Nodes: Maya nodes to process, cmds or Pymel
    :param AsMetaData: bool
    :rtype: [`MExportTags`]
    """
    mTags = []
    found = False
    if not Nodes:
        Nodes = pCore.selected()
    if not issubclass(type(Nodes), list): Nodes = [Nodes]

    for node in Nodes:
        try:
            #see if we have a valid ExportTag already
            if 'MExportTag' in node.metaClass.get():
                mTags.append(eMetaData.MetaData(node))
        except:
            mData = eMetaData.MetaData.m_GetMetaData(node)
            if mData:
                _logger.debug(mData)
                for m in mData:
                    if issubclass(type(m), MExportTag):
                        mTags.append(m)
                        found = True
                        break
    return mTags


def AddExportTag(Node, TagNote):
    """
    Add Export Tag of Type to given nodes. If the current node is already
    tagged then convert that current Tag to an instance of the new type and return it.
    If the Node has an old Tag on it Upgrade and run the conversions on it

    :param Node: Maya Node
    :param TagType: Required TagType Class
    :param TagNote: TagNote string to set on the given

    .. note::

        We need to check UPSTREAM from the given node to ensure that we have NO
        exportTags associated to any parents of the given node before we allow the
        ExportTag to be made. May also need to do the child nodes too......
    """
    MTagType = "MExportTag"
    _logger.info('Required MTagType : %s' % MTagType)

    Node = pCore.PyNode(Node)
    if not any([issubclass(type(Node), pCore.nt.Transform), issubclass(type(Node), pCore.nt.DisplayLayer),
                issubclass(type(Node), pCore.nt.ObjectSet)]):
        raise StandardError("You Can ONLY add ExportTags to TransformNodes")

    if FindExportTagAboveHierarchy([Node.longName()], AsMetaData=True):
        raise StandardError('NESTING TAG WARNING : a PARENT of this object is already Tagged')

    if FindExportTagUnderHierarchy(Node.longName(), AsMetaData=True):
        raise StandardError('NESTING TAG WARNING : a CHILD of this object is already Tagged')
    try:
        mExpTag = MExportTag(Node, TagNote)
    except StandardError, Err:
        _logger.exception(Err)
        raise StandardError('Error adding MExportTag to this node')

    mExpTag.TagNote = TagNote
    return mExpTag

def RemoveExportTags(Nodes):
    """
    Remove ExportTags from the given nodes
    """
    tags = GetExportTagFromSelected(Nodes)
    if tags:
        for tag in tags:
            try:
                tag.m_Delete()
            except:
                _logger.info('Tag Removal Failed : %s' % tag)


def RemoveAllInvalidTags():
    """
    Remove InValid ExportTags from the scene
    """
    AllTags = FindAllMExportTags(AsMetaData=False, ValidOnly=False)
    if AllTags:
        for tag in AllTags:
            if not cmds.listConnections('%s.metaTagged' % tag):
                _logger.info('Removing Invalid Tag : %s' % tag)
                RemoveExportTags(pCore.PyNode(tag))


def SetActiveStateOnGivenTags(Nodes, Active=True):
    """
    Deactivate ExportTags from the given nodes
    """
    tags = GetExportTagFromSelected(Nodes)
    if tags:
        for tag in tags:
            tag.TagActive = Active


def CopyExportTags(Tags):
    """
    Cast available Attrs between the Nodes. This syncs the LoopData too
    """
    MTags = GetExportTagFromSelected(Tags)
    if len(Tags) == 2:
        mTagSource = MTags[0]
        mTagDest = MTags[1]
    else:
        raise StandardError('You need to have 2 tags or Tagged nodes to Copy the Data between')

    attrs = [attr for attr in mTagSource.m_GetMetaNodeAttributes() if
             not attr.longName() in mTagSource._LockedAttributes]
    for attr in attrs:
        try:
            data = attr.longName()
            if mTagDest.MetaNode.hasAttr(data) and not data == 'TagNote':
                current = pCore.PyNode('%s.%s' % (mTagDest.MetaNode, data))
                current.set(attr.get())
        except:
            _logger.info('failed to set attr : %s' % data)

    for loop in mTagSource.GetLoopData():
        try:
            mTagDest.SetLoopData(loop)
        except:
            _logger.info('failed to Copy Loop Data: %s' % loop)


@memo
def getCachedTemplates():
    import taskProcessor.taskList as taskList

    templates = taskList.getTaskTemplates()
    return templates


class HasExportTagError(Exception):
    """
    Exception raised when a node already has an MExportTag attached.

    :param Node: `str` Name of the node that has the MExportTag
    :param MExportClass: `str` Name of the MExportTagClass
    """

    def __init__(self, Node, MExportClass):
        self.msg = "%s already has %s ExportTag" % (Node, MExportClass)



class MExportTag_InterfaceProxy(object):
    """
    This is a wrapper class to replicate the calls on the MExportTag classes below
    but without initializing the MetaData itself. Used for fast searching and UI functions
    to make them fast, if the attr wrapped at this level then a MetaData instance is created and the function / attr
    is looked up on that instance.  So anything we want fast for the UI can be done at this level
    """

    def __init__(self, MetaNode=None):
        self.__MetaNode = MetaNode

    @property
    def MetaNode(self):
        return pCore.PyNode(self.__MetaNode)

    def __getattribute__(self, item):
        try:
            return object.__getattribute__(self, item)
        except:
            metaNode = object.__getattribute__(self, "MetaNode")
            node = eMetaData.MetaData(self.MetaNode)
            return getattr(node, item)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.MetaNode)

    def To_MExportTag(self):
        return eMetaData.MetaData(self.MetaNode)

    @property
    def TagActive(self):
        return self.MetaNode.TagActive.get()

    @TagActive.setter
    def TagActive(self, val):
        self.MetaNode.TagActive.set(bool(val))

    @property
    def TagNote(self):
        return self.MetaNode.TagNote.get()

    @TagNote.setter
    def TagNote(self, val):
        self.MetaNode.TagNote.set(val)

    @property
    def TagType(self):
        try:
            return self.MetaNode.TagType.get()
        except:
            return self.MetaNode.metaClass.get().split("_")[-1]

    def rootNode(self):
        """
        As the mel version for consistency. Return the Tagged MayaNode/Node
        members for layers and sets
        """
        return self.MetaNode.metaTagged.outputs()[0]


class MExportTag(eMetaData.MetaData):
    def __new__(cls, *args, **kw):
        """
        This will now raise an error stopping you adding more than one ExportTag
        to any given Maya Node
        """
        Node = None
        if args:
            Node = pCore.PyNode(args[0])
        if Node:
            mData = eMetaData.MetaData.m_GetMetaData(Node)
            _logger.info('mData: %s' % mData)
            MTag = [m for m in mData if issubclass(type(m), MExportTag)]

            if not MTag:
                try:
                    return super(cls.__class__, cls).__new__(cls)

                except HasExportTagError as err:
                    _logger.warning(err)
                    raise HasExportTagError(Node.name(), mData[0].__class__.__name__)
            else:
                _logger.info('Warning: "%s" : is already connected to MExportTag of Type : %s' % \
                             (Node.name(), MTag[0].__class__.__name__))
                raise HasExportTagError(Node.name(), MTag[0].__class__.__name__)
        else:
            return super(cls.__class__, cls).__new__(cls)


    def __repr__(self):
        return '%s(ExpTag: %s, ExpNode: %s)' % (self.__class__.__name__, self.TagNote, self.rootNode().split('|')[-1])


    def __init__(self, Node=None, TagNote=None, *args, **kws):
        super(MExportTag, self).__init__(Node, *args, **kws)
        self.m_SetInitialProperty("TagNote", TagNote, "")
        self.m_SetInitialProperty("TagActive", True)
        self.m_SetInitialProperty("AutoUpdate", True)
        self.m_SetInitialProperty("TagType", "", "Hidden")  # Pretty print of nodeType, Required for Legacy
        self.m_SetInitialProperty("TaskList", "", "Private")
        self.m_SerializeExportData()
        if TagNote:
            self.MetaNode.rename("%s_%s" % (self.__class__.__name__, TagNote))

    def rename(self, name):
        self.MetaNode.rename("%s_%s" % (self.__class__.__name__, name))

    def rootNode(self):
        """
        Return the Tagged MayaNode
        """
        node = self.m_GetTagged()
        if node:
            return node[0]
        else:
            _logger.info('%s has no rootNode and thus is an invalid tag' % self.MetaNode)
            return ""

    def updateFromTemplate(self, taskListName=""):
        import taskProcessor.taskList as taskList
        import os

        templates = getCachedTemplates()
        exportTag = self
        name = taskListName
        if not name:
            taskList = exportTag.getTaskList(checkForUpdate=False)
            name = taskList.listName

        for k, tl in templates.iteritems():
            for t in tl:
                tName = t.split(".")[0].lower()
                if tName == name.lower():
                    exportTag.setTaskList(os.path.join(k, t))

    def setTaskList(self, taskList_):
        import taskProcessor.taskList as tl
        if isinstance(taskList_, tl.TaskList):
            self.TaskList = taskList_.toJson()
        elif isinstance(taskList_, basestring):
            try:
                self.TaskList = tl.TaskList.fromJson(taskList_)
            except Exception as Err:
                try:
                    self.TaskList = tl.TaskList.fromFile(taskList_).toJson()
                except StandardError as Err:
                    _logger.exception(Err)
                    raise Err

    def getTaskList(self, checkForUpdate=True):
        import taskProcessor.taskList as tl
        import os
        if self.TaskList:
            if all([self.AutoUpdate, checkForUpdate]):
                self.updateFromTemplate()
            return tl.TaskList.fromJson(self.TaskList)
        else:
            templateRoots = tl.getTaskTemplates()
            for t in templateRoots:
                for tt in templateRoots[t]:
                    if os.path.basename(tt).split(".")[0] == self.TagType:
                        filePath = os.path.join(t, tt)
                        return tl.TaskList.fromFile(filePath)


    def m_IsValid(self):
        """
        Generic metaData call over-ridden for ExportTags so just checking RootNode
        """
        if self.rootNode():
            return True
        return False


    def findAllInstances(self):
        """
        From an instance of an ExportTag find all matching Tags of the same Type
        """
        currentClass = self.__class__.__name__.split('.')[-1]
        return [eMetaData.MetaData(m) for m in pCore.ls(type="network") if m.metaClass.get() == currentClass]


    def isReferenced(self):
        return self.MetaNode.isReferenced()