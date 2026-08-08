import json
from dataclasses import replace
import pytest
from campaign_repository import *
from kernel.exceptions import ValidationError

def e(oid="O1",sha="b"*64): return CampaignRepositoryEntry(oid,RepositoryObjectKind.RESULT_SET,sha,"C1","E1")
def put(repo,oid="R1",payload=None): return repo.store_json(object_id=oid,object_kind="result_set",campaign_id="C1",experiment_id="E1",payload=payload or {"x":1})

def test_artifact(): assert ArtifactDescriptor("a","text/plain","a"*64,1,"a.txt").size_bytes==1
def test_artifact_negative():
    with pytest.raises(ValidationError): ArtifactDescriptor("a","text/plain","a"*64,-1,"a.txt")
def test_entry_hash_stable(): assert e().entry_sha256==e().entry_sha256
def test_entry_string_kind(): assert replace(e(),object_kind="result_set").object_kind==RepositoryObjectKind.RESULT_SET
def test_bad_kind():
    with pytest.raises(ValidationError): replace(e(),object_kind="bad")
def test_manifest_count(): assert CampaignRepositoryManifest("R",(e(),)).entry_count==1
def test_manifest_hash_stable(): assert CampaignRepositoryManifest("R",(e(),)).manifest_sha256==CampaignRepositoryManifest("R",(e(),)).manifest_sha256
def test_duplicate_ids():
    with pytest.raises(ValidationError): CampaignRepositoryManifest("R",(e(),e("O1","c"*64)))
def test_duplicate_kind_sha():
    with pytest.raises(ValidationError): CampaignRepositoryManifest("R",(e("O1"),e("O2")))
def test_initialize(tmp_path):
    r=CampaignRepository(tmp_path); r.initialize(); assert (tmp_path/"objects").is_dir()
def test_store(tmp_path): assert put(CampaignRepository(tmp_path)).entry.object_id=="R1"
def test_object_exists(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); assert (tmp_path/x.object_path).is_file()
def test_entry_exists(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); assert (tmp_path/x.entry_path).is_file()
def test_canonical_payload(tmp_path):
    r=CampaignRepository(tmp_path); a=put(r,"A",{"b":2,"a":1}); b=put(r,"B",{"a":1,"b":2}); assert a.entry.object_sha256==b.entry.object_sha256
def test_read(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); assert r.read_object(x.entry)=={"x":1}
def test_verify_entry(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); assert r.verify_entry(x.entry)
def test_tamper(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); (tmp_path/x.object_path).write_text("{}",encoding="utf-8");
    with pytest.raises(ValidationError): r.read_object(x.entry)
def test_safe_component(tmp_path):
    r=CampaignRepository(tmp_path)
    with pytest.raises(ValidationError): r.store_json(object_id="../x",object_kind="result_set",campaign_id="C",experiment_id="E",payload={})
def test_build_manifest(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); assert r.build_manifest(repository_id="R",entries=(x.entry,)).entry_count==1
def test_write_manifest(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); m=r.build_manifest(repository_id="R",entries=(x.entry,)); assert (tmp_path/r.write_manifest(m)).is_file()
def test_verify_manifest(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); m=r.build_manifest(repository_id="R",entries=(x.entry,)); r.write_manifest(m); assert r.verify_manifest(m)
def test_multiple_kinds(tmp_path):
    r=CampaignRepository(tmp_path); a=r.store_json(object_id="E",object_kind="experiment",campaign_id="C",experiment_id="E",payload={}); b=r.store_json(object_id="R",object_kind="execution_run",campaign_id="C",experiment_id="E",payload={}); assert a.entry.object_kind!=b.entry.object_kind
def test_entry_dict(): assert e().to_dict()["schema_version"]=="i1.0"
def test_manifest_dict(): assert CampaignRepositoryManifest("R",()).to_dict()["entry_count"]==0
def test_result_dict(tmp_path): assert put(CampaignRepository(tmp_path)).to_dict()["entry"]["object_id"]=="R1"
def test_missing_object(tmp_path):
    with pytest.raises(FileNotFoundError): CampaignRepository(tmp_path).read_object(e())
def test_empty_manifest(): assert CampaignRepositoryManifest("R",()).entry_count==0
def test_manifest_metadata_changes(): assert CampaignRepositoryManifest("R",(),{"v":1}).manifest_sha256!=CampaignRepositoryManifest("R",(),{"v":2}).manifest_sha256
def test_payload_changes(tmp_path):
    r=CampaignRepository(tmp_path); assert put(r,"A",{"x":1}).entry.object_sha256!=put(r,"B",{"x":2}).entry.object_sha256
def test_dedup(tmp_path):
    r=CampaignRepository(tmp_path); assert put(r,"A").object_path==put(r,"B").object_path
def test_scoped_entry(tmp_path):
    r=CampaignRepository(tmp_path); x=put(r); assert "C1" in x.entry_path and "E1" in x.entry_path
def test_immutable_entry(tmp_path):
    r=CampaignRepository(tmp_path); put(r,"R1");
    with pytest.raises(ValidationError): r.store_json(object_id="R1",object_kind="result_set",campaign_id="C1",experiment_id="E1",payload={"x":1},metadata={"v":2})
def test_kind_values(): assert RepositoryObjectKind.PROVENANCE.value=="provenance"
def test_manifest_order():
    a=e("B","1"*64); b=e("A","2"*64); m=CampaignRepositoryManifest("R",(a,b)); assert [x.object_id for x in m.entries]==["A","B"]
def test_artifact_to_dict(): assert ArtifactDescriptor("a","text/plain","a"*64,1,"a.txt").to_dict()["name"]=="a"
def test_manifest_sha_len(): assert len(CampaignRepositoryManifest("R",()).manifest_sha256)==64
