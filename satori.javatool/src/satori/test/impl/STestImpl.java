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
import satori.test.meta.SXmlParser;
import satori.thrift.STestData;

public class STestImpl implements STestReader {
	private STestSnap snap = null;
	private SId id;
	private SParentProblem problem;
	private String name;
	private SAttributeMap attrs;
	
	private final SDataStatus status = new SDataStatus();
	private final SListener0List data_modified_listeners = new SListener0List();
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
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	
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
		return self;
	}
	public static STestImpl createNew(SParentProblem problem) {
		//TODO: check problem id
		STestImpl self = new STestImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.attrs = SAttributeMap.create(getMetadataInstance().getDefaultAttrs());
		return self;
	}
	
	private boolean check(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (attrs.check(source.getData())) return true;
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
		if (blob == old_blob) return; //TODO: compare blobs
		attrs.setAttr(name, blob != null ? new SBlobAttribute(blob) : null);
		notifyModified();
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
	
	// TODO: Get rid of the following code
	private static final String xml =
		"<checker name=\"Default judge\">" +
		"    <input>" +
		"        <value name=\"time\" description=\"Time limit\" required=\"true\"/>" +
		"        <value name=\"memory\" description=\"Memory limit\" required=\"true\" default=\"1073741824\"/>" +
		"        <file name=\"input\" description=\"Input file\" required=\"true\"/>" +
		"        <file name=\"hint\" description=\"Output/hint file\" required=\"false\"/>" +
		"        <file name=\"checker\" description=\"Checker\" required=\"false\"/>" +
		"    </input>" +
		"</checker>";
	
	private static STestMetadata meta_instance = null;
	
	private static void createMetadata() {
		try { meta_instance = SXmlParser.parse(xml); }
		catch(SXmlParser.ParseException ex) { throw new RuntimeException(ex); }
	}
	public static STestMetadata getMetadataInstance() {
		if (meta_instance == null) createMetadata();
		return meta_instance;
	}
}
