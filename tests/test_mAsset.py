from nose import SkipTest
from nose.tools import assert_equal


import pymel.core as pCore
import tdtools.metaeMAsset as eMAsset


def _Load_ChairMAsset_Simple(force=True):
    _file = "\\\\SERVER9\\Maya-Tools\\testFiles\\eMetaData\\ChairMAsset_Simple.mb"
    if pCore.sceneName() == _file:
        if force:
            pCore.openFile(_file, f=True)
    else:
        pCore.openFile(_file, f=True)

def _getMAssetFromSimpleTestFile(f=True):
    _Load_ChairMAsset_Simple(f)
    return eMAsset.MAsset("MAsset_Chair")


class TestAssetCallbacks:
    def test___init__(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        raise SkipTest # TODO: implement your test here

    def test___new__(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        raise SkipTest # TODO: implement your test here

    def test___repr__(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        # assert_equal(expected, asset_callbacks.__repr__())
        raise SkipTest # TODO: implement your test here

    def test_getMAssetDuplicateState(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        # assert_equal(expected, asset_callbacks.getMAssetDuplicateState())
        raise SkipTest # TODO: implement your test here

    def test_getMAssetRootSelectState(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        # assert_equal(expected, asset_callbacks.getMAssetRootSelectState())
        raise SkipTest # TODO: implement your test here

    def test_setAllCallbacksEnabled(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        # assert_equal(expected, asset_callbacks.setAllCallbacksEnabled(value))
        raise SkipTest # TODO: implement your test here

    def test_setMAssetDuplicateEnabled(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        # assert_equal(expected, asset_callbacks.setMAssetDuplicateEnabled(value))
        raise SkipTest # TODO: implement your test here

    def test_setMAssetRootSelectEnabled(self):
        # asset_callbacks = AssetCallbacks(*args, **kwargs)
        # assert_equal(expected, asset_callbacks.setMAssetRootSelectEnabled(value))
        raise SkipTest # TODO: implement your test here

class TestUpdateAllMAssetMenus:
    def test_update_all_m_asset_menus(self):
        # assert_equal(expected, UpdateAllMAssetMenus(onReferenced))
        raise SkipTest # TODO: implement your test here

class TestMAssetGlobalOptionsDialog:
    def test_m_asset_global_options_dialog(self):
        # assert_equal(expected, MAssetGlobalOptionsDialog())
        raise SkipTest # TODO: implement your test here

class TestInstallFilterArrayRootTransformMelProcedure:
    def test_install__filter_array__root_transform__mel_procedure(self):
        # assert_equal(expected, Install_FilterArray_RootTransform_MelProcedure())
        raise SkipTest # TODO: implement your test here

class TestMassetFilterOutliner:
    def test_masset__filter_outliner(self):
        # assert_equal(expected, Masset_FilterOutliner())
        raise SkipTest # TODO: implement your test here

class TestMAssetToggleFilterOutliner:
    def test_m_asset__toggle_filter_outliner(self):
        # assert_equal(expected, MAsset_ToggleFilterOutliner())
        raise SkipTest # TODO: implement your test here

class TestMAssetFilterArrayRootTransform:
    def test_m_asset__filter_array__root_transform(self):
        # assert_equal(expected, MAsset_FilterArray_RootTransform(nodes))
        raise SkipTest # TODO: implement your test here

class TestMAssetFilterRootTransform:
    def test_m_asset__filter_root_transform(self):
        # assert_equal(expected, MAsset_FilterRootTransform(name))
        raise SkipTest # TODO: implement your test here

class TestMAssetFilterNonRootTransform:
    def test_m_asset__filter_non_root_transform(self):
        # assert_equal(expected, MAsset_FilterNonRootTransform(name))
        raise SkipTest # TODO: implement your test here

class TestMAssetDuplicateSelectedAssets:
    def test_m_asset__duplicate_selected_assets(self):
        # assert_equal(expected, MAsset_DuplicateSelectedAssets(select))
        raise SkipTest # TODO: implement your test here

class TestMAssetOptimiseUnused:
    def test_m_asset__optimise_unused(self):
        # assert_equal(expected, MAsset_OptimiseUnused())
        raise SkipTest # TODO: implement your test here

class TestMAssetGetMAssetFrom:
    def test_m_asset__get_m_asset_from(self):
        # assert_equal(expected, MAsset_GetMAssetFrom(Node))
        raise SkipTest # TODO: implement your test here

class TestMAssetGetNonRootMembers:
    def test_m_asset__get_non_root_members(self):
        # assert_equal(expected, MAsset_GetNonRootMembers(MAssetNode))
        raise SkipTest # TODO: implement your test here

class TestMAssetGetRootTransform:
    def test_m_asset__get_root_transform(self):
        # assert_equal(expected, MAsset_GetRootTransform(MAssetNode))
        raise SkipTest # TODO: implement your test here

class TestMAssetIsRootTransform:
    def test_m_asset__is_root_transform(self):
        # assert_equal(expected, MAsset_IsRootTransform(name))
        raise SkipTest # TODO: implement your test here

class TestMAssetGetMAssetPartAttr:
    def test_m_asset__get_m_asset_part_attr(self):
        # assert_equal(expected, MAsset_GetMAssetPartAttr(name))
        raise SkipTest # TODO: implement your test here

class TestRBMDecoratorToMAsset:
    def test_r_b_m__decorator__to_m_asset(self):
        # assert_equal(expected, RBM_Decorator_ToMAsset(func))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbUpdateAsset:
    def test_m_asset__rmb__update_asset(self):
        # assert_equal(expected, MAsset_Rmb_UpdateAsset(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbUpdateAllUnderMouseById:
    def test_m_asset__rmb__update_all_under_mouse_by_id(self):
        # assert_equal(expected, MAsset_Rmb_UpdateAllUnderMouseById(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbSelectAllRootTransformsById:
    def test_m_asset__rmb__select_all_root_transforms_by_id(self):
        # assert_equal(expected, MAsset_Rmb_SelectAllRootTransformsById(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbSelectMAsset:
    def test_m_asset__rmb__select_m_asset(self):
        # assert_equal(expected, MAsset_Rmb_SelectMAsset(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbSelectRootTransform:
    def test_m_asset__rmb__select_root_transform(self):
        # assert_equal(expected, MAsset_Rmb_SelectRootTransform(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbSelectAssetMembers:
    def test_m_asset__rmb__select_asset_members(self):
        # assert_equal(expected, MAsset_Rmb_SelectAssetMembers(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbSelectNonRootMembers:
    def test_m_asset__rmb__select_non_root_members(self):
        # assert_equal(expected, MAsset_Rmb_SelectNonRootMembers(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbDuplicate:
    def test_m_asset__rmb__duplicate(self):
        # assert_equal(expected, MAsset_Rmb_Duplicate(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetRmbDissolve:
    def test_m_asset__rmb__dissolve(self):
        # assert_equal(expected, MAsset_Rmb_Dissolve(Asset))
        raise SkipTest # TODO: implement your test here

class TestMAssetUtils:
    def TestAutoAssetScene(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.AutoAssetScene())
        raise SkipTest # TODO: implement your test here

    def TestContaineriseMAsset(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.ContaineriseMAsset(MAssetObj))
        raise SkipTest # TODO: implement your test here

    def TestFindMAssetsIn(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.FindMAssetsIn(Nodes))
        raise SkipTest # TODO: implement your test here

    def TestGetAllMAssets(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.GetAllMAssets(GroupById, UUID))
        raise SkipTest # TODO: implement your test here

    def TestGetDataBaseAssetObject(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.GetDataBaseAssetObject(Id))
        raise SkipTest # TODO: implement your test here

    def TestGetMAssetsBy_DatabaseId(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.GetMAssetsBy_DatabaseId(Id))
        raise SkipTest # TODO: implement your test here

    def TestImportAssetFromAssetDb(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.ImportAssetFromAssetDb(AssetObj, AutoAsset, MergeMaterials, DeleteUnused, MakeContainer))
        raise SkipTest # TODO: implement your test here

    def TestImportAutoAsset(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.ImportAutoAsset(ImportedNodes, AssetObj))
        raise SkipTest # TODO: implement your test here

    def TestMergeImportedLayers(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.MergeImportedLayers(newNodes))
        raise SkipTest # TODO: implement your test here

    def TestMergeLayer(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.MergeLayer(KeepLayer, DeleteLayer))
        raise SkipTest # TODO: implement your test here

    def TestMergeMAssetMaterials(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.MergeMAssetMaterials(MAssetObj))
        raise SkipTest # TODO: implement your test here

    def TestReplaceSelectedWith(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.ReplaceSelectedWith(AssetObj, **kw))
        raise SkipTest # TODO: implement your test here

    def TestSnapAsset(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.SnapAsset(A, B))
        raise SkipTest # TODO: implement your test here

    def TestUpdateAll(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.UpdateAll())
        raise SkipTest # TODO: implement your test here

    def TestUpdateAssets(self):
        # m_asset_utils = MAssetUtils()
        # assert_equal(expected, m_asset_utils.UpdateAssets(mAssetList, assetObj, maintainName, forceMaintainName))
        raise SkipTest # TODO: implement your test here

class TestMAsset:
    def TestAddAssetMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.AddAssetMembers(Node))
        raise SkipTest # TODO: implement your test here

    def TestAutoSetRoot(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.AutoSetRoot())
        raise SkipTest # TODO: implement your test here

    def TestCopyMAssetDbAttrs(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.CopyMAssetDbAttrs(NewAsset))
        raise SkipTest # TODO: implement your test here

    def TestDelete(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.Delete(doBasicOptimise))
        raise SkipTest # TODO: implement your test here

    def TestDissolve(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.Dissolve())
        raise SkipTest # TODO: implement your test here

    def TestDuplicateAsset(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.DuplicateAsset())
        raise SkipTest # TODO: implement your test here

    def TestDuplicateParts(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.DuplicateParts(Nodes))
        raise SkipTest # TODO: implement your test here

    def TestGetAllCollisionMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetAllCollisionMembers())
        raise SkipTest # TODO: implement your test here

    def TestGetAssetMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetAssetMembers())
        raise SkipTest # TODO: implement your test here

    def TestGetAssetShadingGroups(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetAssetShadingGroups())
        raise SkipTest # TODO: implement your test here

    def TestGetAssetTimeStamp(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetAssetTimeStamp())
        raise SkipTest # TODO: implement your test here

    def TestGetBulletCollisionMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetBulletCollisionMembers())
        raise SkipTest # TODO: implement your test here

    def TestGetCollisionMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetCollisionMembers())
        raise SkipTest # TODO: implement your test here

    def TestGetMAsset(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetMAsset(Node, AsMetaData))
        raise SkipTest # TODO: implement your test here

    def TestGetNonRootMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetNonRootMembers())
        raise SkipTest # TODO: implement your test here

    def TestGetPathModifiedDate(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetPathModifiedDate())
        raise SkipTest # TODO: implement your test here

    def TestGetPlayerCollisionMembers(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetPlayerCollisionMembers())
        raise SkipTest # TODO: implement your test here

    def TestGetRootTransform(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.GetRootTransform())
        raise SkipTest # TODO: implement your test here

    def TestIsAssetMember(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.IsAssetMember(Node))
        raise SkipTest # TODO: implement your test here

    def TestIsOutOfDate(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.IsOutOfDate())
        raise SkipTest # TODO: implement your test here

    def TestIsRootTransform(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.IsRootTransform(Node))
        raise SkipTest # TODO: implement your test here

    def TestRefreshUUID(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.RefreshUUID())
        raise SkipTest # TODO: implement your test here

    def TestSetAssetDbObj(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.SetAssetDbObj(AssetDbObj))
        raise SkipTest # TODO: implement your test here

    def TestSetName(self):
        m_asset = _getMAssetFromSimpleTestFile(f=False)
        m_asset.SetName("SimpleChair")
        assert_equal(m_asset.MetaNode.name(), "MAsset_SimpleChair")

    def TestSetRootTransform(self):
        # m_asset = MAsset(Node, Name, Selection, **kw)
        # assert_equal(expected, m_asset.SetRootTransform(Node))
        raise SkipTest # TODO: implement your test here

    def test___init__(self):
        m_asset = _getMAssetFromSimpleTestFile(f=True)
        assert isinstance(m_asset, eMAsset.MAsset)


class TestRegisterMAssetFunctions:
    def test_register_m_asset_functions(self):
        # assert_equal(expected, RegisterMAssetFunctions(force))
        raise SkipTest # TODO: implement your test here

