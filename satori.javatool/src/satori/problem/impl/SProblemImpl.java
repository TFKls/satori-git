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
import satori.task.SResultTask;
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
	public static SProblemImpl createRemote(SProblemList problem_list, SProblemSnap snap) throws STaskException {
		SProblemImpl self = new SProblemImpl(problem_list);
		self.snap = snap;
		snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.reload();
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
	
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		if (test_list_listener != null) test_list_listener.call(null);
		if (suite_list_listener != null) suite_list_listener.call(null);
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
	
	private static class FullProblem {
		private final SProblemReader problem;
		private final List<STestBasicReader> tests;
		private final List<STestSuiteBasicReader> suites;
		public SProblemReader getProblem() { return problem; }
		public List<STestBasicReader> getTests() { return tests; }
		public List<STestSuiteBasicReader> getTestSuites() { return suites; }
		public FullProblem(SProblemReader problem, List<STestBasicReader> tests, List<STestSuiteBasicReader> suites) {
			this.problem = problem;
			this.tests = tests;
			this.suites = suites;
		}
	}
	public void reload() throws STaskException {
		FullProblem source = STaskManager.execute(new SResultTask<FullProblem>() {
			@Override public FullProblem run() throws Exception {
				SProblemReader problem = SProblemData.load(getId());
				List<STestBasicReader> tests = STestData.list(getId());
				List<STestSuiteBasicReader> suites = STestSuiteData.list(getId());
				return new FullProblem(problem, tests, suites);
			}
		});
		name = source.getProblem().getName();
		desc = source.getProblem().getDescription();
		notifyUpToDate();
		snap.set(this);
		//snap.createLists(); //TODO: what the hell is this?
		snap.getTestList().load(source.getTests());
		snap.getTestSuiteList().load(source.getTestSuites());
	}
	public void create() throws STaskException {
		id = STaskManager.execute(new SResultTask<SId>() {
			@Override public SId run() throws Exception {
				 return new SId(SProblemData.create(SProblemImpl.this));
			}
		});
		notifyUpToDate();
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
		notifyUpToDate();
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
