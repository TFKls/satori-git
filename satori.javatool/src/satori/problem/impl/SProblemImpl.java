package satori.problem.impl;

import java.util.ArrayList;
import java.util.List;

import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SException;
import satori.common.SId;
import satori.common.SListener1;
import satori.common.SReference;
import satori.common.SView;
import satori.problem.SParentProblem;
import satori.problem.SProblemList;
import satori.problem.SProblemReader;
import satori.problem.SProblemSnap;
import satori.problem.STestList;
import satori.problem.STestSuiteList;
import satori.thrift.SProblemData;

public class SProblemImpl implements SProblemReader, SParentProblem {
	private final SProblemList problem_list;
	
	private SProblemSnap snap;
	private SId id;
	private String name;
	private String desc;
	
	private final SDataStatus status = new SDataStatus();
	private final List<SView> views = new ArrayList<SView>();
	private final SReference reference = new SReference() {
		@Override public void notifyModified() { snapModified(); }
		@Override public void notifyDeleted() { snapDeleted(); }
	};
	private SListener1<STestList> test_list_listener = null;
	private SListener1<STestSuiteList> suite_list_listener = null;
	
	@Override public boolean hasId() { return id.isSet(); }
	@Override public long getId() { return id.get(); }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	
	@Override public STestList getTestList() { return snap.getTestList(); }
	@Override public STestSuiteList getTestSuiteList() { return snap.getTestSuiteList(); }
	
	private SProblemImpl(SProblemList problem_list) {
		this.problem_list = problem_list;
	}
	
	public static SProblemImpl create(SProblemList problem_list, SProblemSnap snap) throws SException {
		SProblemImpl self = new SProblemImpl(problem_list);
		self.snap = snap;
		self.snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.name = snap.getName();
		self.desc = snap.getDescription();
		return self;
	}
	public static SProblemImpl createNew(SProblemList problem_list) {
		SProblemImpl self = new SProblemImpl(problem_list);
		self.snap = null;
		self.id = new SId();
		self.name = "";
		self.desc = "";
		return self;
	}
	
	private boolean check(SProblemReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (!source.getDescription().equals(desc)) return true;
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
		test_list_listener.call(null);
		suite_list_listener.call(null);
	}
	
	public void setName(String name) {
		if (this.name.equals(name)) return;
		this.name = name;
		notifyModified();
	}
	public void setDescription(String desc) {
		if (this.desc.equals(desc)) return;
		this.desc = desc;
		notifyModified();
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
	
	public void setTestListListener(SListener1<STestList> listener) {
		SAssert.assertNull(test_list_listener, "Test list listener already set");
		test_list_listener = listener;
		if (snap != null) listener.call(snap.getTestList());
	}
	public void setTestSuiteListListener(SListener1<STestSuiteList> listener) {
		SAssert.assertNull(suite_list_listener, "Test suite list listener already set");
		suite_list_listener = listener;
		if (snap != null) listener.call(snap.getTestSuiteList());
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
	
	public void reload() throws SException {
		SAssert.assertTrue(isRemote(), "Problem not remote");
		snap.reload();
		name = snap.getName();
		desc = snap.getDescription();
		notifyUpToDate();
	}
	public void create() throws SException {
		SAssert.assertFalse(isRemote(), "Problem already created");
		id.set(SProblemData.create(this));
		notifyUpToDate();
		snap = SProblemSnap.create(this);
		snap.addReference(reference);
		test_list_listener.call(snap.getTestList());
		suite_list_listener.call(snap.getTestSuiteList());
		problem_list.addProblem(snap);
	}
	public void save() throws SException {
		SAssert.assertTrue(isRemote(), "Problem not remote");
		SProblemData.save(this);
		notifyUpToDate();
		snap.set(this);
	}
	public void delete() throws SException {
		SAssert.assertTrue(isRemote(), "Problem not remote");
		SProblemData.delete(getId());
		problem_list.removeProblem(snap);
		snap.notifyDeleted(); //calls snapDeleted
	}
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		snap = null;
		test_list_listener.call(null);
		suite_list_listener.call(null);
	}
}
