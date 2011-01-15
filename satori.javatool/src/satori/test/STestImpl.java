package satori.test;

import java.util.ArrayList;
import java.util.List;

import satori.attribute.SAttribute;
import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;
import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SException;
import satori.common.SId;
import satori.common.SReference;
import satori.common.SView;
import satori.common.SViewList;
import satori.problem.SParentProblem;
import satori.server.STestData;

public class STestImpl implements STestReader {
	private STestSnap snap = null;
	private SId id;
	private SParentProblem problem;
	private String name;
	private SAttributeMap attrs;
	
	private final List<Input> inputs = new ArrayList<Input>();
	private final SDataStatus status = new SDataStatus();
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
		getMetadataInstance().createTestCase(self);
		self.updateInputs();
		return self;
	}
	public static STestImpl createNew(SParentProblem problem) {
		//TODO: check problem id
		STestImpl self = new STestImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.attrs = SAttributeMap.create(getMetadataInstance().getDefaultAttrs());
		getMetadataInstance().createTestCase(self);
		self.updateInputs();
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
	public void setAttr(String name, SAttribute attr) {
		//TODO: check if not equal
		attrs.setAttr(name, attr);
		notifyModified();
	}
	
	public Input getInput(InputMetadata meta) {
		for (Input input : inputs) if (input.getMetadata() == meta) return input;
		return null;
	}
	public void addInput(Input input) { inputs.add(input); }
	
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
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	private void updateInputs() {
		for (Input input : inputs) input.update();
	}
	
	public void reload() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		snap.reload();
		name = snap.getName();
		attrs = SAttributeMap.create(snap.getData());
		updateInputs();
		notifyUpToDate();
	}
	public void create() throws SException {
		SAssert.assertFalse(isRemote(), "Test already created");
		id.set(STestData.create(this));
		updateInputs();
		notifyUpToDate();
		snap = STestSnap.create(this);
		snap.addReference(reference);
		problem.getTestList().addTest(snap);
	}
	public void save() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		STestData.save(this);
		updateInputs();
		notifyUpToDate();
		snap.set(this);
	}
	public void delete() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		STestData.delete(getId());
		id.clear();
		updateInputs();
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
		"<test>" +
		"    <input name=\"time\" description=\"Time limit\" type=\"value\" required=\"true\" default_value=\"10000\" />" +
		"    <input name=\"memory\" description=\"Memory limit\" type=\"value\" required=\"true\" default_value=\"1073741824\" />" +
		"    <input name=\"input\" description=\"Input file\" type=\"file\" required=\"true\" />" +
		"    <input name=\"hint\" description=\"Output/hint file\" type=\"file\" required=\"false\" />" +
		"    <input name=\"checker\" description=\"Checker\" type=\"file\" required=\"false\" />" +
		"</test>";
	
	private static TestCaseMetadata meta_instance = null;
	
	private static void createMetadata() {
		try { meta_instance = XmlParser.parse(xml); }
		catch(XmlParser.ParseException ex) { throw new RuntimeException(ex); }
	}
	public static TestCaseMetadata getMetadataInstance() {
		if (meta_instance == null) createMetadata();
		return meta_instance;
	}
}
