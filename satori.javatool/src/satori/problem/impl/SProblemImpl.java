package satori.problem.impl;

import java.util.ArrayList;
import java.util.List;

import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SId;
import satori.common.SListener1;
import satori.common.SReference;
import satori.common.SView;
import satori.data.SProblemData;
import satori.data.STestData;
import satori.data.STestSuiteData;
import satori.problem.SParentProblem;
import satori.problem.SProblemList;
import satori.problem.SProblemReader;
import satori.problem.SProblemSnap;
import satori.problem.STestList;
import satori.problem.STestSuiteBasicReader;
import satori.problem.STestSuiteList;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskManager;
import satori.test.STestBasicReader;

public class SProblemImpl implements SProblemReader, SParentProblem {
	private final SProblemList problem_list;
	
	private SProblemSnap snap = null;
	private SId id = SId.unset();
	private String name = "";
	private String desc = "";
	
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
	
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		if (test_list_listener != null) test_list_listener.call(null);
		if (suite_list_listener != null) suite_list_listener.call(null);
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
	
	private class LoadTask implements STask {
		public SProblemReader problem;
		public List<STestBasicReader> tests;
		public List<STestSuiteBasicReader> suites;
		@Override public void run() throws Exception {
			problem = SProblemData.load(getId());
			tests = STestData.list(getId());
			suites = STestSuiteData.list(getId());
		}
	}
	public void reload() throws STaskException {
		LoadTask task = new LoadTask();
		STaskManager.execute(task);
		name = task.problem.getName();
		desc = task.problem.getDescription();
		status.markUpToDate();
		updateViews();
		snap.set(this);
		snap.createLists();
		snap.getTestList().load(task.tests);
		snap.getTestSuiteList().load(task.suites);
	}
	public void create() throws STaskException {
		STaskManager.execute(new STask() {
			@Override public void run() throws Exception {
				id = new SId(SProblemData.create(SProblemImpl.this));
			}
		});
		status.markUpToDate();
		updateViews();
		snap = SProblemSnap.create(this);
		snap.addReference(reference);
		test_list_listener.call(snap.getTestList());
		suite_list_listener.call(snap.getTestSuiteList());
		problem_list.addProblem(snap);
	}
	public void save() throws STaskException {
		STaskManager.execute(new STask() {
			@Override public void run() throws Exception {
				SProblemData.save(SProblemImpl.this);
			}
		});
		status.markUpToDate();
		updateViews();
		snap.set(this);
	}
	public void delete() throws STaskException {
		STaskManager.execute(new STask() {
			@Override public void run() throws Exception {
				SProblemData.delete(getId());
			}
		});
		problem_list.removeProblem(snap);
		snap.notifyDeleted(); //calls snapDeleted
	}
}
