import pymel.core as pCore
import tdtools.eMeta as eMeta
from tdtools.eMeta import eMExportTag as mTag

import maya.cmds as cmds
import os

MAYA_TEST_FILES_DIR = "\\\\server9\\Maya-Tools\\testFiles\\eMExportTag\\"

class TestFindTagData():

    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "FindTagTypes.ma", f=True)

    def test_FindExportTags(self):
        Tags=sorted(mTag.FindExportTags())
        assert [t.TagNote for t in Tags]==['CAM_01',
                                           'MRIG',
                                           'SimpleEntity',
                                           'EntityGrp',
                                           'Entity_PerFrame',
                                           'ProgressiveMorphTester',
                                           'Trig',
                                           'VFX_EntityGrp',
                                           'Zone']
        
        assert [t.TagType for t in Tags]==['Camera',
                                           'Character',
                                           'Entity',
                                           'EntityGroup',
                                           'EntityPerFrame',
                                           'ProgressiveMorph',
                                           'Trigger',
                                           'VFXGroup',
                                           'Zone']
        
        assert [t.rootNode().name() for t in Tags]==['Test_MasterCam',
                                                     'GameRoot',
                                                     'Test_SimpleEntity',
                                                     'Test_EntityGrp',
                                                     'Test_Entity_PerFrame',
                                                     'Test_ProgressiveMorphTester',
                                                     'Test_TriggerLoc',
                                                     'VFX_EntityGrp',
                                                     'Test_Zone']
        
        assert isinstance(Tags[0],mTag.MExportTag_Camera), 'Tag is not MExportTag_Camera'
        assert isinstance(Tags[1],mTag.MExportTag_Character), 'Tag is not MExportTag_Character'
        assert isinstance(Tags[2],mTag.MExportTag_Entity), 'Tag is not MExportTag_Entity'
        assert isinstance(Tags[3],mTag.MExportTag_EntityGroup), 'Tag is not MExportTag_EntityGroup'
        assert isinstance(Tags[4],mTag.MExportTag_EntityPerFrame), 'Tag is not MExportTag_EntityPerFrame'
        assert isinstance(Tags[5],mTag.MExportTag_ProgressiveMorph), 'Tag is not MExportTag_ProgressiveMorph'
        assert isinstance(Tags[6],mTag.MExportTag_Trigger), 'Tag is not MExportTag_Trigger'
        assert isinstance(Tags[7],mTag.MExportTag_VFXGroup), 'Tag is not MExportTag_VFXGroup'
        assert isinstance(Tags[8],mTag.MExportTag_Zone), 'Tag is not MExportTag_Zone'
        
    def test_FindExportTags_ofType(self):
        Tags=mTag.FindExportTags(TagType=['Camera','Character'])
        assert [t.TagNote for t in sorted(Tags)]==['CAM_01','MRIG']
        
    def test_FindExportTags_ofName(self):
        Tags=mTag.FindExportTags(SearchTags=['Trig','VFX_EntityGrp'])
        assert [t.rootNode() for t in sorted(Tags)]==['Test_TriggerLoc','VFX_EntityGrp']
        
    def test_FindExportTags_active(self):
        Tags=mTag.FindExportTags(Active=True)
        assert [t.TagNote for t in sorted(Tags)]==[ 'CAM_01',
                                                    'MRIG',
                                                    'SimpleEntity',
                                                    'EntityGrp',
                                                    'ProgressiveMorphTester',
                                                    'Trig',
                                                    'VFX_EntityGrp',
                                                    'Zone']
    def test_FindExportTags_rLongName(self):
        Tags=sorted(mTag.FindExportTags(ReturnType='LongName'))
        assert sorted(Tags)==['|Test_CharacterRig_01|MASTER_NODE|ScaleNode|GameRoot',            
                     '|Test_EntityGrp',
                     '|Test_Entity_PerFrame',
                     '|Test_MasterCam',
                     '|Test_ProgressiveMorphTester',
                     '|Test_SimpleEntity',
                     '|Test_TriggerLoc',
                     '|Test_Zone',
                     '|VFX_EntityGrp']
        
    def test_FindExportTags_rTagNote(self):
        Tags=mTag.FindExportTags(ReturnType='TagNote')
        assert sorted(Tags)==['CAM_01',
                        'EntityGrp',
                        'Entity_PerFrame',
                        'MRIG',
                        'ProgressiveMorphTester',
                        'SimpleEntity',
                        'Trig',
                        'VFX_EntityGrp',
                        'Zone']
        
    def test_FindExportTags_rNodes(self):
        Tags=mTag.FindExportTags(ReturnType='Nodes')
        assert sorted(Tags)==['GameRoot',
                              'Test_EntityGrp',
                              'Test_Entity_PerFrame',
                              'Test_MasterCam',
                              'Test_ProgressiveMorphTester',
                              'Test_SimpleEntity',
                              'Test_TriggerLoc',
                              'Test_Zone',
                              'VFX_EntityGrp']   
        
#    def test_FindAllMExportTags(self):
#        Tags=mTag.FindAllMExportTags()
#        eq_(Tags,)
#        
#    def test_FindAllProxyExportTags(self):
#        Tags=mTag.FindAllProxyExportTags()
#        eq_(Tags,)
        
    def test_FindExportTagsOfType(self):
        Tags=mTag.FindExportTagsOfType('Zone')
        assert sorted(Tags)==['|Test_Zone']
        
    def test_FindExportTagUnderHierarchy(self):
        Tags=mTag.FindExportTagUnderHierarchy('Test_CharacterRig_01')
        assert Tags==['|Test_CharacterRig_01|MASTER_NODE|ScaleNode|GameRoot']
    
    def test_FindExportTagAboveHierarchy(self):
        Tags=mTag.FindExportTagAboveHierarchy(Nodes=['Area_A3_pSphere7','EntGrp_pSphere6'])
        assert sorted(Tags)==['|Test_EntityGrp', '|Test_Zone']  
             
    def test_FindExportTagAboveHierarchyNoNodes(self):
        cmds.select(['Area_A3_pSphere7','EntGrp_pSphere6'])
        Tags=mTag.FindExportTagAboveHierarchy()
        assert sorted(Tags)==['|Test_EntityGrp', '|Test_Zone']   
   
    def test_FindExportTagAboveHierarchy_Character(self):
        Tags=mTag.FindExportTagAboveHierarchy(Nodes=['R_Wrist_Ctr'])
        assert sorted(Tags)==['|Test_CharacterRig_01|MASTER_NODE|ScaleNode|GameRoot']
        
    def test_FindActiveTriggerShifter(self):
        #run in the mel world as a pre-process to shift the scene
        Tag=mTag.FindActiveTriggerShifter('MTags')
        assert isinstance(Tag, mTag.MExportTag_Trigger)
        assert mTag.FindActiveTriggerShifter('LongName')=='|Test_TriggerLoc'
        assert mTag.FindActiveTriggerShifter('Nodes')=='Test_TriggerLoc'
        Tag.TriggerShift=0
        assert not mTag.FindActiveTriggerShifter('LongName')
        Tag.TriggerShift=1

        
    def test_FindExportTimeNodes(self):
        assert [t.MetaNode for t in mTag.FindExportTimeNodes(ReturnType="MTimes")]==['End',
                                                                                    'MExportTimeRange',
                                                                                    'Middle',
                                                                                    'Start'] 
        assert mTag.FindExportTimeNodes(ReturnType="TimeRange")==[1.0, 110.0],'OverAll TimeRange incorrect'
        assert mTag.FindExportTimeNodes(Start=30, End=60)[0].TimeStamp=='Middle'
        assert mTag.FindExportTimeNodes(Start=61)[0].TimeStamp=='End'
        assert mTag.FindExportTimeNodes(End=60)[0].TimeStamp=='Middle'
        assert [t.MetaNode for t in mTag.FindExportTimeNodes(TimeStamp=['Middle'])]==['Middle']
        assert [t.MetaNode for t in mTag.FindExportTimeNodes(TimeStamp=['Middle','End'])]==['End','Middle']
                
    def test_GetExportTagFromSelected_Cmds(self):
        Tag=mTag.GetExportTagFromSelected('Test_Zone')[0]
        assert isinstance(Tag,mTag.MExportTag_Zone)
        assert Tag.TagNote=='Zone'
        assert Tag.rootNode()=='Test_Zone'
        assert Tag.TagType=='Zone'

    def test_GetExportTagFromSelected_PyNode(self):
        Tag=mTag.GetExportTagFromSelected(pCore.PyNode('GameRoot'))[0]
        assert isinstance(Tag,mTag.MExportTag_Character)
        assert Tag.TagNote=='MRIG'
        assert Tag.rootNode()=='GameRoot'
        assert Tag.TagType=='Character'
        
    def test_GetLoopData_FromSelected_asTime(self):
        Tag=mTag.GetExportTagFromSelected('GameRoot')[0]
        loops=Tag.GetLoopData(AsTime=True)
        assert [loop.MetaNode for loop in loops]==['Middle','Start','End','MExportTimeRange']
        assert [loop.TimeStamp for loop in loops]== ['Middle', 'Start', 'End', '']
        
    def test_GetLoopData_FromSelected_asString(self):
        Tag=mTag.GetExportTagFromSelected('GameRoot')[0]
        loops=Tag.GetLoopData(AsTime=False)
        result=[(name,'%0.2f' % start,'%0.2f' % end) for name,start,end in loops]
        assert result== [('Middle', '30.00', '60.00'), ('Start', '1.00', '22.00'), ('End', '61.00', '100.00'), ('', '101.00', '110.00')]
      
    def test_GetTimeOutputRanges(self):
        Tag=mTag.GetExportTagFromSelected('GameRoot')[0]
        result=[(name,'%0.2f' % start,'%0.2f' % end) for name,start,end in Tag.GetTimeOutputRanges()]
        assert result==[('Middle', '30.00', '60.00'), ('Start', '1.00', '22.00'), ('End', '61.00', '100.00'), ('', '101.00', '110.00')]
        Tag=mTag.GetExportTagFromSelected('Test_EntityGrp')[0]      
        assert Tag.GetTimeOutputRanges()==[('__timelines__', 1.0, 24.0)],\
                        'TimeOutputRanges incorrect, even without loopData this should return an output time for the exporter'
        
class TestAddTagData():
    
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "FindTagTypes.ma", f=True)
        self.TestTag = None
    
    def teardown(self):
        try:
            self.TestTag.m_Delete()
        except:
            pass
           
    def test_AddEntityTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Entity', 'EntityTag')
        assert self.TestTag.MetaNode.name()=='EXP_EntityTag'
        assert self.TestTag.TagNote=='EntityTag'
        assert self.TestTag.TagType=='Entity'
        assert self.TestTag.rootNode()=='NewNode'
        assert isinstance(self.TestTag, mTag.MExportTag_Entity)
        
        #Change the TagType via the Add call
        self.TestTag=mTag.AddExportTag('NewNode', 'Character', 'ChangedTagType')
        assert isinstance(self.TestTag, mTag.MExportTag_Character)
        assert self.TestTag.rootNode()=='NewNode'
        #assert self.TestTag.MetaNode.name()=='EXP_ChangedTagType'
        assert self.TestTag.TagType=='Character'
        
    def test_AddEntityGrpTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'EntityGroup', 'EntityGrpTag')
        assert self.TestTag.MetaNode=='EXP_EntityGrpTag'
        assert self.TestTag.TagNote=='EntityGrpTag'
        assert self.TestTag.TagType=='EntityGroup'
        assert isinstance(self.TestTag, mTag.MExportTag_EntityGroup)
        
    def test_AddCameraTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Camera', 'CameraTag')
        assert self.TestTag.MetaNode=='EXP_CameraTag'
        assert self.TestTag.TagNote=='CameraTag'
        assert self.TestTag.TagType=='Camera'
        assert isinstance(self.TestTag,mTag.MExportTag_Camera)
        
    def test_AddCharacterTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Character', 'CharacterAdded')
        assert self.TestTag.MetaNode=='EXP_CharacterAdded'
        assert self.TestTag.TagNote=='CharacterAdded'
        assert self.TestTag.TagType=='Character'
        assert isinstance(self.TestTag,mTag.MExportTag_Character)
        
    def test_AddTriggerTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Trigger', 'TriggerAdded')
        assert self.TestTag.MetaNode=='EXP_TriggerAdded'
        assert self.TestTag.TagNote=='TriggerAdded'
        assert self.TestTag.TagType=='Trigger'
        assert isinstance(self.TestTag,mTag.MExportTag_Trigger)
        
    def test_AddZoneTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Zone', 'ZoneAdded')
        assert self.TestTag.MetaNode=='EXP_ZoneAdded'
        assert self.TestTag.TagNote=='ZoneAdded'
        assert self.TestTag.TagType=='Zone'
        assert isinstance(self.TestTag,mTag.MExportTag_Zone)
        
    def test_AddVFXGroupTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'VFXGroup', 'VFXGroupAdded')
        assert self.TestTag.MetaNode=='EXP_VFXGroupAdded'
        assert self.TestTag.TagNote=='VFXGroupAdded'
        assert self.TestTag.TagType=='VFXGroup'
        assert isinstance(self.TestTag,mTag.MExportTag_VFXGroup)
        
    def test_AddProgressiveMorphTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'ProgressiveMorph', 'ProgressiveMorphAdded')
        assert self.TestTag.MetaNode=='EXP_ProgressiveMorphAdded'
        assert self.TestTag.TagNote=='ProgressiveMorphAdded'
        assert self.TestTag.TagType=='ProgressiveMorph'
        assert isinstance(self.TestTag,mTag.MExportTag_ProgressiveMorph)
        
    def test_AddEntityPerFrameTag(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'EntityPerFrame', 'EntityPerFrameAdded')
        assert self.TestTag.MetaNode=='EXP_EntityPerFrameAdded'
        assert self.TestTag.TagNote=='EntityPerFrameAdded'
        assert self.TestTag.TagType=='EntityPerFrame'
        assert isinstance(self.TestTag,mTag.MExportTag_EntityPerFrame)       
        
    def test_AddExportTagsByNodeName(self):
        self.TestTag=mTag.AddExportTagsByNodeName(['NewNode'],'Entity')[0]
        assert self.TestTag.MetaNode.name()=='EXP_NewNode'
        assert self.TestTag.TagNote=='NewNode'
        assert self.TestTag.TagType=='Entity'
        assert self.TestTag.rootNode()=='NewNode'
        assert isinstance(self.TestTag, mTag.MExportTag_Entity)
        
    def test_AddNestedChildTag(self):
        #This is setup to fail, we're trying to add a child Tag when one of the 
        #parent nodes is already Tagged. We DO NOT allow Nested Tag
        try:
            self.TestTag=mTag.AddExportTag('Area_A3_pSphere6', 'Entity', 'EntityFailure')
            assert False,'ERROR: was able to initialize a Nested Tag as a Child of another'   
        except:  
            assert True     
            
    def test_HasExportTagError(self):
        self.TestTag=mTag.MExportTag_Base(pCore.PyNode('NewNode'),'Entity')
        try:
            self.TestTag=mTag.MExportTag_Base('NewNode')  
            assert False, 'shouldnt be able to take an instance of a Tag for a node that already has a tag'
        except mTag.HasExportTagError:
            assert True
        except:
            assert False, 'wrong ERROR thrown'
             
    def test_NewBlockTest(self):
        self.TestTag=mTag.MExportTag_Base()
        assert self.TestTag.m_IsValid()==False
            
    def test_RemoveExportTags(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Entity', 'EntityTag')
        assert self.TestTag.MetaNode=='EXP_EntityTag'
        mTag.RemoveExportTags('NewNode')
        assert not mTag.GetExportTagFromSelected(pCore.PyNode('NewNode'))
        
    def test_CopyExportTags(self):
        pass
        
    # Loop =================================================  
    def test_AddLoopData(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Entity', 'EntityTag')
        loop=self.TestTag.AddLoopData('NewLoop',23,46)
        assert isinstance(loop,mTag.MExportTimeRange), 'loop isnt a TimeRange object'
        assert loop.Start==23, 'Loop start incorrect'
        assert loop.End==46, 'Loop end incorrect'
        assert loop.TimeStamp=='NewLoop', 'Loop TimeStamp incorrect'
        self.TestTag.RemoveLoopData()
 
    def test_AddLoopOfCurrentTime(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Entity', 'EntityTag')
        currentLoop=mTag.FindExportTimeNodes()[0]
        loop=self.TestTag.AddLoopData('NewLoop',currentLoop.Start,currentLoop.End,Force=True)
        assert self.TestTag.GetLoopData()[0].MetaNode==loop.MetaNode
        
    def test_SetLoopData(self):
        self.TestTag=mTag.AddExportTag('NewNode', 'Entity', 'EntityTag')
        loop=mTag.FindExportTimeNodes()[0]
        self.TestTag.SetLoopData(loop)
        assert self.TestTag.GetLoopData()

    def test_AddLoopDataFromVisibility(self):
        pass
    
    # Overrides ============================================= 
    def test_AddOverRides(self): 
        Tag=mTag.GetExportTagFromSelected('Test_Zone')[0] 
        includers=[pCore.PyNode(node) for node in ['Area_A1_pSphere4','Area_A2_pSphere6','Area_A3_pSphere4','Area_A3_pSphere5']]
        excluders=[pCore.PyNode(node) for node in ['Area_A1_pSphere2','Area_A2_pSphere4','Area_A3_pSphere2','Area_A3_pSphere3']]
        
        Tag.AddOverRides(Nodes=includers,State='Include')
        Tag.AddOverRides(Nodes=excluders,State='Exclude')
        assert Tag.GetOverRides(State='Include')==includers
        assert Tag.GetOverRides(State='Exclude')==excluders
        allOverrides=list(excluders)
        allOverrides.extend(includers)
        assert sorted(Tag.GetOverRides())==sorted(allOverrides)
        
        Tag.SetOverRides(includers,'Exclude')
        assert not Tag.GetOverRides(State='Include')
        assert Tag.GetOverRides(State='Exclude')==sorted(allOverrides)
        assert sorted(Tag.GetOverRides())==sorted(allOverrides)
        
        Tag.DeleteOverRides()
        assert Tag.GetOverRides()==[]
       
        
class Test_BaseClass():
    
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "FindTagTypes.ma", f=True)
        self.Tag=mTag.GetExportTagFromSelected('GameRoot')[0]
        self.Tag.m_Delete()
        self.Tag=mTag.AddExportTag('GameRoot', 'Character', 'MRIG')
        self.Tag.AddLoopData('TestLoop',23,46)
        self.Tag.AddOverRides(Nodes=[pCore.PyNode('L_Leg')])
        
    def teardown(self):  
        #ReAdd a clean ExportTag so we don't worry about modifying it
        try:
            self.Tag.m_Delete()
            self.Tag=mTag.AddExportTag('GameRoot', 'Character', 'MRIG')
            self.Tag.AddLoopData('TestLoop',23,46)
            self.Tag.AddOverRides(Nodes=[pCore.PyNode('L_Leg')])
        except:
            pass
        
    def test_MTagType(self):
        assert isinstance(self.Tag,mTag.MExportTag_Character) 
           
    def test_RootNode(self):
        root=self.Tag.rootNode()
        assert isinstance(root, pCore.nodetypes.Joint),'This should return a PyNode'
        assert root.name()=='GameRoot'
        
    def test_ExtraSelectionMethod(self):
        assert self.Tag.GetExtraSelectionMethod()==0
        self.Tag.SetExtraSelectionMethod(2) 
        assert self.Tag.GetExtraSelectionMethod()==2
        self.Tag.SetExtraSelectionMethod(0)
        
    def test_RenameTag(self):
        self.Tag.RenameTag('FooBarButtChomp')
        assert self.Tag.MetaNode=='EXP_FooBarButtChomp'

    def test_ConvertTagType(self):
        new=self.Tag.ConvertTagType('Entity')
        assert isinstance(new, mTag.MExportTag_Entity) 
        assert new.MetaNode=='EXP_MRIG'  
        assert new.TagNote=='MRIG'

    def test_m_Delete(self):
        mNode=self.Tag.rootNode()
        loop=self.Tag.GetLoopData()[0].MetaNode
        overRide= self.Tag.GetOverRides()[0]
        self.Tag.m_Delete()
        assert not mNode.hasAttr('ExportSpecific'),'The Legacy Tag should have been removed in the delete'
        assert not pCore.objExists(loop), 'This LoopNode should have beed Garbaged by the m_Delete'
        assert not overRide.hasAttr('OverrideMarker'),'OverRider Attr Not cleaned by the Delete'
        
        
class Test_ProcessHandlers():
    
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "FindTagTypes.ma", f=True)
    
    def test_CharacterFilter(self):
        Tag=mTag.FindExportTags(TagType='Character')[0]
        nodes=Tag._ProcessBaseTagFilter()
        assert [n.name() for n in nodes]==['GameRoot',
                                           'Head',
                                           'Neck',
                                           'L_Thumb3',
                                           'L_Thumb2',
                                           'L_Thumb',
                                           'L_Index_Finger3',
                                           'L_Index_Finger2',
                                           'L_Index_Finger',
                                           'L_Second_Finger3',
                                           'L_Second_Finger2',
                                           'L_Second_Finger',
                                           'L_Third_Finger3',
                                           'L_Third_Finger2',
                                           'L_Third_Finger',
                                           'L_Little_Finger3',
                                           'L_Little_Finger2',
                                           'L_Little_Finger',
                                           'L_Wrist',
                                           'L_Arm_Lower',
                                           'L_Arm_Upper',
                                           'L_Arm',
                                           'L_ComplexScap',
                                           'R_Thumb3',
                                           'R_Thumb2',
                                           'R_Thumb',
                                           'R_Index_Finger3',
                                           'R_Index_Finger2',
                                           'R_Index_Finger',
                                           'R_Second_Finger3',
                                           'R_Second_Finger2',
                                           'R_Second_Finger',
                                           'R_Third_Finger3',
                                           'R_Third_Finger2',
                                           'R_Third_Finger',
                                           'R_Little_Finger3',
                                           'R_Little_Finger2',
                                           'R_Little_Finger',
                                           'R_Wrist',
                                           'R_Arm_Lower',
                                           'R_Arm_Upper',
                                           'R_Arm',
                                           'R_ComplexScap',
                                           'Shoulders',
                                           'Spine_2',
                                           'Spine_1',
                                           'Spine',
                                           'L_Toe',
                                           'L_Foot',
                                           'L_Leg_Lower',
                                           'L_Leg',
                                           'R_Toe',
                                           'R_Foot',
                                           'R_Leg_Lower',
                                           'R_Leg',
                                           'Root']  
    def test_GetMCharacter(self):
        tag=mTag.GetExportTagFromSelected('GameRoot')[0]
        MChar=tag.GetMCharacter()
        assert isinstance(MChar,meta.eMCharacter.MCharacter)
    
    def test_GetMSRCExport(self):
        tag=mTag.GetExportTagFromSelected('GameRoot')[0]
        MChar=tag.GetMSRC_Export()
        assert isinstance(MChar,meta.eMCharacter.MSRC)

    def test_EntityFilter(self):
        Tag=mTag.FindExportTags(TagType='Entity')[0]
        nodes=Tag._ProcessBaseTagFilter()
        assert [n.name() for n in nodes]==['Test_SimpleEntity']
        
    def test_EntityGrpFilter(self):
        Tag=mTag.FindExportTags(TagType='EntityGroup')[0]
        nodes=Tag._ProcessBaseTagFilter()
        assert [n.name() for n in nodes]==['Test_EntityGrp',
                                           'EntGrp_pSphere2',
                                           'EntGrp_pSphere3',
                                           'EntGrp_pSphere4',
                                           'EntGrp_pSphere5',
                                           'EntGrp_pSphere6',
                                           'EntGrp_pSphere7']
    
    def test_CameraFilter(self):
        Tag=mTag.FindExportTags(TagType='Camera')[0]
        nodes=Tag._ProcessBaseTagFilter()
        assert [n.name() for n in nodes]==['Test_MasterCam']
    
    def test_VFXGroupFilter(self):
        Tag=mTag.FindExportTags(TagType='VFXGroup')[0]
        nodes=Tag._ProcessBaseTagFilter()
        assert [n.name() for n in nodes]==['VFX_EntityGrp',
                                           'VFX_pSphere2',
                                           'VFX_pSphere3',
                                           'VFX_pSphere4',
                                           'VFX_pSphere5',
                                           'VFX_pSphere6',
                                           'VFX_pSphere7']
    def test_ZoneFilter(self): 
        Tag=mTag.FindExportTags(TagType='Zone')[0]
        nodes=Tag._ProcessBaseTagFilter()
        assert [n.name() for n in nodes]==['Area_A1_pSphere2',
                                           'Area_A1_pSphere3',
                                           'Area_A1_pSphere4',
                                           'Area_A1_pSphere5',
                                           'Area_A1_pSphere6',
                                           'Area_A1_pSphere7',
                                           'Area_1',
                                           'Area_A2_pSphere2',
                                           'Area_A2_pSphere3',
                                           'Area_A2_pSphere4',
                                           'Area_A2_pSphere5',
                                           'Area_A2_pSphere6',
                                           'Area_A2_pSphere7',
                                           'Area_2',
                                           'Area_A3_pSphere2',
                                           'Area_A3_pSphere3',
                                           'Area_A3_pSphere4',
                                           'Area_A3_pSphere5',
                                           'Area_A3_pSphere6',
                                           'Area_A3_pSphere7',
                                           'Area_3']
    

    def test_MainProcessHandlerCall(self):
        '''
        This is the one responsible for all the Override, roothandling, samplespace etc..
        each individual class then has it's own initial filter which is passed into this
        '''
        pCore.melGlobals.initVar('string','ExportFormat')
        pCore.melGlobals['ExportFormat']="COLLADA_Rev2"
        Tag=mTag.FindExportTags(TagType='EntityGroup')[0]
        nodes=sorted(Tag.ProcessSelectionFilter())
        assert [n.name() for n in nodes]==['EntGrp_pSphere2',
                                           'EntGrp_pSphere4',
                                           'EntGrp_pSphere5',
                                           'EntGrp_pSphere7',
                                           'Test_EntityGrp']
    
    def test_ProcessHandler_ExtraMethod2(self):
        Tag=mTag.FindExportTags(TagType='Character')[0]
        Tag.SetExtraSelectionMethod(2)
        nodes=Tag.ProcessSelectionFilter()
        assert pCore.PyNode('ScaleNode') in nodes
        assert Tag.SelectionFilter
        Tag.SetExtraSelectionMethod(0)
        Tag._CleanupProcessedTagFilter()
        assert not Tag.SelectionFilter
    
    def test_SetEL4SerializedSelection_Base(self):
        Tag=mTag.FindExportTags(TagType='EntityGroup')[0]
        Tag.ProcessSelectionFilter()
        
        result=set(Tag.SelectionFilter.split(','))
        expected=set(['Test_EntityGrp','EntGrp_pSphere5','EntGrp_pSphere4','EntGrp_pSphere7','EntGrp_pSphere2'])
        assert expected==result
        Tag._ClearEl4SerializedSelection()
        assert Tag.SelectionFilter==''
    
    def test_SetEL4SerializedSelection_Zone(self):
        #Zone SelectionFilter is over-ridden so only child Entity's are returned, entity's 
        #below these are merged polygroups in EL4 world so not included
        Tag=mTag.FindExportTags(TagType='Zone')[0]
        Tag.ProcessSelectionFilter()
        assert Tag.SelectionFilter=='Area_1,Area_2,Area_3'
        Tag._ClearEl4SerializedSelection()
           
    def test_SelectionHints(self):
        cmds.select(['Area_A2_pSphere4','Area_A2_pSphere5','Area_A2_pSphere6','Area_A1_pSphere3','Area_A1_pSphere6'])
        hint=mTag.MExportHint()
        hint.AddNodesToHint(pCore.selected())
        assert sorted(hint.Members())==['Area_A1_pSphere3','Area_A1_pSphere6','Area_A2_pSphere4','Area_A2_pSphere5','Area_A2_pSphere6']
        assert isinstance(mTag.MExportHint.FindHint(), mTag.MExportHint)
        hint.DeleteHint()
        assert not mTag.MExportHint.FindHint()


class Test_SpecialCaseTags():
    
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "SpecialCaseTags.ma", f=True)
        
    def teardown(self):
        #we're screwing with the scene so lets make sure we reload after each test!!!!!!!
        pCore.openFile(MAYA_TEST_FILES_DIR + "SpecialCaseTags.ma", f=True)

    def test_AddLoopDataFromVisibility(self):
        '''
        From the given tag cast it's keyed visibilty into loopTag data
        NOTE: This uses the _GetKeyedVisibilityNode funct which is overloaded for characters
        '''
        tag=mTag.GetExportTagFromSelected(pCore.PyNode('VisibilityCastTest'))[0]
        assert tag._GetKeyedVisibilityNode()=='VisibilityCastTest'
        loops=tag.AddLoopDataFromVisibility()
        assert [loop.__repr__() for loop in loops]==['MExportTimeRange(TimeStamp: "Vis_00", Start: 22.78, End: 55.78)',
                                                        'MExportTimeRange(TimeStamp: "Vis_01", Start: 80.0, End: 129.0)',
                                                        'MExportTimeRange(TimeStamp: "Vis_02", Start: 158.0, End: 159.0)',
                                                        'MExportTimeRange(TimeStamp: "Vis_03", Start: 230.0, End: 275.0)',
                                                        'MExportTimeRange(TimeStamp: "Vis_04", Start: 290.0, End: 290.0)']
        result=[(name,'%0.2f' % start,'%0.2f' % end) for name,start,end in tag.GetLoopData(AsTime=False)]
        assert result==[('Vis_01', '80.00', '129.00'),
                        ('Vis_00', '22.78', '55.78'),
                        ('Vis_02', '158.00', '159.00'),
                        ('Vis_03', '230.00', '275.00'),
                        ('Vis_04', '290.00', '290.00')]
        
    def test_AddActiveTimeData(self):
        '''
        The VFX Tag has an extra attr "ManageEL4TimelineVis" which determines if the Visibility
        of each node should be derived from its keyed visibility state. This is then cast to an
        attr on the node and subsequently serialized to Collada
        '''
        tag=mTag.GetExportTagFromSelected(pCore.PyNode('vfx_visiblityDataCast'))[0]
        nodes=tag._ProcessBaseTagFilter()
        
        result=['%s,on:%0.2f,off:%0.2f' % (node.name(),node.TimelineStart.get(),node.TimelineEnd.get()) for node in nodes]
        expected=['pSphere2,on:1.00,off:19.00',
                  'pSphere3,on:20.00,off:31.00',
                  'pSphere4,on:32.00,off:49.00',
                  'pSphere5,on:50.00,off:70.00',
                  'pSphere6,on:71.00,off:85.00',
                  'pSphere7,on:71.00,off:101.00',
                  'pSphere8,on:102.00,off:117.00',
                  'pSphere9,on:118.00,off:136.00',
                'pSphere10,on:137.00,off:137.00']
        assert result==expected
        assert not [node for node in nodes \
                    if not node.SerializeForExport.get()=='[["TimelineStart", "TimelineStart", false],["TimelineEnd", "TimelineEnd", false]]']
        #Try removing the data added
        for node in nodes:
            mTag.RemoveActiveTimeData(node)
        assert not [node for node in nodes if node.hasAttr('TimelineStart') \
                    or node.hasAttr('TimelineEnd')  or node.hasAttr('SerializeForExport')]
            
    def test_ProgressiveMorphFilter(self):
        '''
        Test the convertion of the deformerData to linear blendshape
        '''
        pCore.playbackOptions(min=1, max=50)
        tag=mTag.GetExportTagFromSelected(pCore.PyNode('pCube1'))[0]
        data=tag._ProcessBaseTagFilter()
        
        #Note the actual Tagged Node is NOT passed into the filtered nodes!
        assert data==['pCube1_progressive']
        
        #Test the generated Progressive network
        node=data[0]
        shape=node.getShape()
        shape.listHistory(type='mesh')
        blendshape=shape.listHistory(type='blendShape')[0]
        assert blendshape.name()=='blendShape1'
        assert blendshape.getTarget()==['Progressive_1',
                                 'Progressive_2',
                                 'Progressive_3',
                                 'Progressive_4',
                                 'Progressive_5',
                                 'Progressive_6',
                                 'Progressive_7',
                                 'Progressive_8',
                                 'Progressive_9',
                                 'Progressive_10',
                                 'Progressive_11',
                                 'Progressive_12',
                                 'Progressive_13',
                                 'Progressive_14',
                                 'Progressive_15',
                                 'Progressive_16',
                                 'Progressive_17',
                                 'Progressive_18',
                                 'Progressive_19',
                                 'Progressive_20',
                                 'Progressive_21',
                                 'Progressive_22',
                                 'Progressive_23',
                                 'Progressive_24',
                                 'Progressive_25',
                                 'Progressive_26',
                                 'Progressive_27',
                                 'Progressive_28',
                                 'Progressive_29',
                                 'Progressive_30',
                                 'Progressive_31',
                                 'Progressive_32',
                                 'Progressive_33',
                                 'Progressive_34',
                                 'Progressive_35',
                                 'Progressive_36',
                                 'Progressive_37',
                                 'Progressive_38',
                                 'Progressive_39',
                                 'Progressive_40',
                                 'Progressive_41',
                                 'Progressive_42',
                                 'Progressive_43',
                                 'Progressive_44',
                                 'Progressive_45',
                                 'Progressive_46',
                                 'Progressive_47',
                                 'Progressive_48',
                                 'Progressive_49',
                                 'Progressive_50']

    def test_EntityPerFrame(self):
        '''
        Test the conversion to single visibility switched nodes
        '''
        pCore.playbackOptions(min=1, max=50)
        tag=mTag.GetExportTagFromSelected(pCore.PyNode('pCube1'))[0]
        tag=tag.ConvertTagType('EntityPerFrame')
        data=tag._ProcessBaseTagFilter()
        
        #Test that the new nodes have the TimeLine Data cast over to them
        firstTenResults=['%s,on:%0.2f,off:%0.2f' % (node.name(),node.TimelineStart.get(),node.TimelineEnd.get()) for node in sorted(data)[:10]]
        assert firstTenResults==['EntityPerFrame_1,on:1.00,off:2.00',
                                 'EntityPerFrame_10,on:10.00,off:11.00',
                                 'EntityPerFrame_11,on:11.00,off:12.00',
                                 'EntityPerFrame_12,on:12.00,off:13.00',
                                 'EntityPerFrame_13,on:13.00,off:14.00',
                                 'EntityPerFrame_14,on:14.00,off:15.00',
                                 'EntityPerFrame_15,on:15.00,off:16.00',
                                 'EntityPerFrame_16,on:16.00,off:17.00',
                                 'EntityPerFrame_17,on:17.00,off:18.00',
                                 'EntityPerFrame_18,on:18.00,off:19.00']
        
        expected=['EntityPerFrame_1',
                 'EntityPerFrame_10',
                 'EntityPerFrame_11',
                 'EntityPerFrame_12',
                 'EntityPerFrame_13',
                 'EntityPerFrame_14',
                 'EntityPerFrame_15',
                 'EntityPerFrame_16',
                 'EntityPerFrame_17',
                 'EntityPerFrame_18',
                 'EntityPerFrame_19',
                 'EntityPerFrame_2',
                 'EntityPerFrame_20',
                 'EntityPerFrame_21',
                 'EntityPerFrame_22',
                 'EntityPerFrame_23',
                 'EntityPerFrame_24',
                 'EntityPerFrame_25',
                 'EntityPerFrame_26',
                 'EntityPerFrame_27',
                 'EntityPerFrame_28',
                 'EntityPerFrame_29',
                 'EntityPerFrame_3',
                 'EntityPerFrame_30',
                 'EntityPerFrame_31',
                 'EntityPerFrame_32',
                 'EntityPerFrame_33',
                 'EntityPerFrame_34',
                 'EntityPerFrame_35',
                 'EntityPerFrame_36',
                 'EntityPerFrame_37',
                 'EntityPerFrame_38',
                 'EntityPerFrame_39',
                 'EntityPerFrame_4',
                 'EntityPerFrame_40',
                 'EntityPerFrame_41',
                 'EntityPerFrame_42',
                 'EntityPerFrame_43',
                 'EntityPerFrame_44',
                 'EntityPerFrame_45',
                 'EntityPerFrame_46',
                 'EntityPerFrame_47',
                 'EntityPerFrame_48',
                 'EntityPerFrame_49',
                 'EntityPerFrame_5',
                 'EntityPerFrame_50',
                 'EntityPerFrame_6',
                 'EntityPerFrame_7',
                 'EntityPerFrame_8',
                 'EntityPerFrame_9'] 
        
        assert [n.name() for n in sorted(data)]==expected
        toClean=['EntityPerFrame']
        toClean.extend(expected)
        assert sorted(pCore.melGlobals['NodesToDeleteOnCleanUp'])==toClean
        
        #test the Cleanup calls
        tag._CleanupProcessedTagFilter()
        assert not pCore.melGlobals['NodesToDeleteOnCleanUp']
        assert not [n for n in data if pCore.PyNode(n).exists()]
                                                   
   
class TestSampleSpace():
    
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "SampleSpace.ma", f=True)

    def test_GetSampleSpace(self):
        #check this nodes SampleSpace setup
        pCore.select('joint1')
        Tag=mTag.GetExportTagFromSelected()[0]
        ss=Tag.GetSampleSpace()
        assert isinstance(ss, mTag.MExportTag_EntityGroup)
        assert ss.MetaNode=='EXP_Car'
        assert Tag.GetSampleSpace(TagOnly=False)=='|CarGroup'

    def test_GetChildSampleSpace(self):
        #Check for child SampleSpaces
        pCore.select('CarGroup')
        Tag=mTag.GetExportTagFromSelected()[0]
        assert Tag.GetChildSampleSpace()==['EXP_Crate2', 'EXP_Driver']
        assert [t.MetaNode for t in Tag.GetChildSampleSpace(AsMetaData=True)]==['EXP_Crate2', 'EXP_Driver']==['EXP_Crate2', 'EXP_Driver']
        
    def test_DeleteSampleSpaceRef(self):
        Tag=mTag.GetExportTagFromSelected('CarGroup')[0]
        assert Tag.GetChildSampleSpace()==['EXP_Crate2', 'EXP_Driver']
        Tag.DeleteSampleSpaceRef()
        assert not Tag.GetChildSampleSpace()
        #Reset the scene as we've destroyed it here
        self.setup()
    
    def test_GetDirectChildSampleSpace(self):
        pass
    
    def test_SetDirectSampleSpace(self):
        pass

            
    
class TestMelCalls():
    
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "FindTagTypes.ma", f=True)
        
    def test_ReturnTagDataAsString(self):
        pCore.melGlobals.initVar('string','eBatchProcessType')
        pCore.melGlobals['eBatchProcessType']="Tag"
        assert mTag.ReturnTagDataAsString('Test_EntityGrp')=='EntityGrp||EntityGroup||True||none||0'
    
    def test_ReturnTagData(self):
        assert mTag.ReturnTagData('GameRoot')==['MRIG', 'Character', True, 'none', 0, True, True]
        
    def test_ReturnTagData_DisplayLayer(self):
        pCore.melGlobals.initVar('string','eBatchProcessType')
        pCore.melGlobals['eBatchProcessType']="DisplayLayer"
        assert mTag.ReturnTagData('Control_Nodes')==['Control_Nodes', 'displayLayer', 'True', 'none']
            
    def test_ReturnLoopDataFromSelected_given(self):
        assert mTag.ReturnLoopDataFromSelected('GameRoot')==['Middle',
                                                             '30.0',
                                                                '60.0',
                                                                'Start',
                                                                '1.0',
                                                                '22.0',
                                                                'End',
                                                                '61.0',
                                                                '100.0',
                                                                '',
                                                                '101.0',
                                                                '110.0']
    def test_ReturnLoopDataFromSelected(self):
        cmds.select('GameRoot')
        assert mTag.ReturnLoopDataFromSelected()==['Middle',
                                                    '30.0',
                                                    '60.0',
                                                    'Start',
                                                    '1.0',
                                                    '22.0',
                                                    'End',
                                                    '61.0',
                                                    '100.0',
                                                    '',
                                                    '101.0',
                                                    '110.0']     
        
    def test_ProcessExportTagFilter(self):
        assert sorted(mTag.ProcessExportTagFilter('Test_EntityGrp'))==[u'|Test_EntityGrp',
                                                                       '|Test_EntityGrp|EntGrp_pSphere2',
                                                                       '|Test_EntityGrp|EntGrp_pSphere4',
                                                                       '|Test_EntityGrp|EntGrp_pSphere5',
                                                                       '|Test_EntityGrp|EntGrp_pSphere7']
    def test_ProcessExportTagFilter_DisplayLayer(self):    
        assert sorted(mTag.ProcessExportTagFilter('Control_Nodes'))==['|Test_CharacterRig_01|MASTER_NODE|ScaleNode|Controls_Ctr']
        
    
          
class Test_ProxyLegacyCalls():
        
    def setup(self):
        pCore.openFile(MAYA_TEST_FILES_DIR + "FindTagTypes.ma", f=True)
        
    def test_A_BaseProxyTest(self):
        Tag=mTag.FindAllProxyExportTags()[0]
        assert Tag.TagActive
        assert Tag.TagNote=='proxyLegacy'
        assert Tag.TagObj=='Old_ProxyTag'
        assert Tag.TagType=='Entity'
        assert Tag.rootNode()=='Old_ProxyTag'
        assert Tag.GetTimeOutputRanges()== [('__timelines__', 1.0, 24.0)]
        
    def test_B_ConvertScene(self):
        current=mTag.FindExportTags()
        mTag.ConvertSceneToMetaTags()
        new=mTag.FindExportTags()
        assert not new==current
        converted=mTag.GetExportTagFromSelected(pCore.PyNode('Old_ProxyTag'))[0]
        assert isinstance(converted,mTag.MExportTag_Entity)
                
                
