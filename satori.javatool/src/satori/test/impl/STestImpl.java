package satori.test.impl;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;
import satori.attribute.SBlobAttribute;
import satori.attribute.SStringAttribute;
import satori.blob.SBlob;
import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SException;
import satori.common.SId;
import satori.common.SListener0;
import satori.common.SListener0List;
import satori.common.SReference;
import satori.common.SView;
import satori.common.SViewList;
import satori.problem.SParentProblem;
import satori.test.STestReader;
import satori.test.STestSnap;
import satori.test.meta.STestMetadata;
import satori.thrift.STestData;

public class STestImpl implements STestReader {
	private STestSnap snap = null;
	private SId id;
	private SParentProblem problem;
	private String name;
	private SAttributeMap attrs;
	private STestMetadata meta;
	
	private final SDataStatus status = new SDataStatus();
	private final SListener0List data_modified_listeners = new SListener0List();
	private final SListener0List metadata_modified_listeners = new SListener0List();
	private final SViewList views = new SViewList();
	private final SReference reference = new SReference() {
		@Override public void notifyModified() { snapModified(); }
		@Override public void notifyDeleted() { snapDeleted(); }
	};
	
	@Override public boolean hasId() { return id.isSet(); }
	@Override public long getId() { return id.get(); }
	@Override public long getProblemId() { return problem.getId(); }
	@Override public String getName() { return name; }
	@Override public SAttributeReader getData() { return attrs; }
	public SBlob getJudge() { return attrs.getBlob("judge"); }
	public STestMetadata getMetadata() { return meta; }
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	public boolean isProblemRemote() { return problem.hasId(); }
	
	private STestImpl() {}
	
	public static STestImpl create(STestSnap snap, SParentProblem problem) throws SException {
		//TODO: check problem id
		if (!snap.isComplete()) snap.reload();
		STestImpl self = new STestImpl();
		self.snap = snap;
		self.snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.problem = problem;
		self.name = snap.getName();
		self.attrs = SAttributeMap.create(snap.getData());
		self.meta = STestMetadata.get(self.attrs.getBlob("judge"));
		return self;
	}
	public static STestImpl createNew(SParentProblem problem) {
		STestImpl self = new STestImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.meta = STestMetadata.getDefault();
		self.attrs = SAttributeMap.create(self.meta.getDefaultAttrs());
		return self;
	}
	
	private boolean check(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (!attrs.equals(source.getData())) return true;
		return false;
	}
	
	private void snapModified() {
		if (!check(snap)) return;
		notifyOutdated();
	}
	private void snapDeleted() {
		snap = null;
		id.clear();
		notifyOutdated();
	}
	
	public void setName(String name) {
		if (this.name.equals(name)) return;
		this.name = name;
		notifyModified();
	}
	public void setDataString(String name, String value) {
		String old_value = attrs.getString(name);
		if (value == null && old_value == null) return;
		if (value != null && value.equals(old_value)) return;
		attrs.setAttr(name, value != null ? new SStringAttribute(value) : null);
		notifyModified();
		callDataModifiedListeners();
	}
	public void setDataBlob(String name, SBlob blob) {
		SBlob old_blob = attrs.getBlob(name);
		if (blob == null && old_blob == null) return;
		if (blob != null && blob.equals(old_blob)) return;
		attrs.setAttr(name, blob != null ? new SBlobAttribute(blob) : null);
		notifyModified();
		callDataModifiedListeners();
	}
	public void setJudge(SBlob judge) throws SException {
		SBlob old_judge = attrs.getBlob("judge");
		if (judge == null && old_judge == null) return;
		if (judge != null && judge.equals(old_judge)) return;
		meta = STestMetadata.get(judge);
		attrs = SAttributeMap.create(meta.getDefaultAttrs());
		attrs.setAttr("judge", judge != null ? new SBlobAttribute(judge) : null);
		notifyModified();
		callMetadataModifiedListeners();
		callDataModifiedListeners();
	}
	
	private void notifyModified() {
		status.markModified();
		updateViews();
	}
	private void notifyOutdated() {
		status.markOutdated();
		updateViews();
	}
	private void notifyUpToDate() {
		status.markUpToDate();
		updateViews();
	}
	
	public void addDataModifiedListener(SListener0 listener) { data_modified_listeners.add(listener); }
	public void removeDataModifiedListener(SListener0 listener) { data_modified_listeners.remove(listener); }
	private void callDataModifiedListeners() { data_modified_listeners.call(); }
	
	public void addMetadataModifiedListener(SListener0 listener) { metadata_modified_listeners.add(listener); }
	public void removeMetadataModifiedListener(SListener0 listener) { metadata_modified_listeners.remove(listener); }
	private void callMetadataModifiedListeners() { metadata_modified_listeners.call(); }
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void reload() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		snap.reload();
		name = snap.getName();
		attrs = SAttributeMap.create(snap.getData());
		notifyUpToDate();
		callDataModifiedListeners();
	}
	public void create() throws SException {
		SAssert.assertFalse(isRemote(), "Test already created");
		id.set(STestData.create(this));
		notifyUpToDate();
		snap = STestSnap.create(this);
		snap.addReference(reference);
		problem.getTestList().addTest(snap);
	}
	public void save() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		STestData.save(this);
		notifyUpToDate();
		snap.set(this);
	}
	public void delete() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		STestData.delete(getId());
		id.clear();
		notifyOutdated();
		snap.removeReference(reference);
		snap.notifyDeleted();
		problem.getTestList().removeTest(snap);
		snap = null;
	}
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		snap = null;
	}
}
