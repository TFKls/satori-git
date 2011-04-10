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
	
	private SProblemSnap snap = null;
	private volatile SId id = SId.unset();
	private volatile String name = "";
	private volatile String desc = "";
	
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
	
	@Override public synchronized STestList getTestList() { return snap.getTestList(); }
	@Override public synchronized STestSuiteList getTestSuiteList() { return snap.getTestSuiteList(); }
	
	private SProblemImpl(SProblemList problem_list) {
		this.problem_list = problem_list;
	}
	
	public static SProblemImpl createNew(SProblemList problem_list) {
		return new SProblemImpl(problem_list);
	}
	public static SProblemImpl createRemote(SProblemList problem_list, SProblemSnap snap) {
		SProblemImpl self = new SProblemImpl(problem_list);
		self.snap = snap;
		snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.status.markOutdated();
		return self;
	}
	
	// To be called from synchronized methods
	private boolean check(SProblemReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (!source.getDescription().equals(desc)) return true;
		return false;
	}
	
	private synchronized void snapModified() {
		if (!check(snap)) return;
		notifyOutdated();
	}
	private synchronized void snapDeleted() {
		id = SId.unset();
		notifyOutdated();
		snap = null;
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
	
	public synchronized void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		test_list_listener.call(null);
		suite_list_listener.call(null);
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
	
	public void reload() throws SException {
		SProblemReader source = SProblemData.load(id.get());
		name = source.getName();
		desc = source.getDescription();
		status.markUpToDate();
		updateViews();
		snap.set(this);
		snap.createLists();
		snap.getTestList().reload();
		snap.getTestSuiteList().reload();
	}
	public void create() throws SException {
		id = new SId(SProblemData.create(this));
		status.markUpToDate();
		updateViews();
		snap = SProblemSnap.create(SProblemImpl.this);
		snap.addReference(reference);
		test_list_listener.call(snap.getTestList());
		suite_list_listener.call(snap.getTestSuiteList());
		problem_list.addProblem(snap);
	}
	public void save() throws SException {
		SProblemData.save(SProblemImpl.this);
		status.markUpToDate();
		updateViews();
		snap.set(this);
	}
	public void delete() throws SException {
		SProblemData.delete(getId());
		problem_list.removeProblem(snap);
		snap.notifyDeleted(); //calls snapDeleted
	}
}
