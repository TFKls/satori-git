package satori.problem.impl;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SException;
import satori.common.SId;
import satori.common.SList;
import satori.common.SReference;
import satori.common.SView;
import satori.common.SViewList;
import satori.problem.SParentProblem;
import satori.problem.STestSuiteReader;
import satori.problem.STestSuiteSnap;
import satori.test.STestBasicReader;
import satori.test.STestSnap;
import satori.test.impl.STestImpl;
import satori.thrift.STestSuiteData;

public class STestSuiteImpl implements STestSuiteReader {
	private STestSuiteSnap snap = null;
	private SId id;
	private SParentProblem problem;
	private String name;
	private String desc;
	private List<STestImpl> tests;
	
	private SList<STestImpl> pane = null;
	
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
	@Override public String getDescription() { return desc; }
	@Override public Iterable<STestImpl> getTests() { return tests; }
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	public boolean isProblemRemote() { return problem.hasId(); }
	public boolean hasNonremoteTests() {
		for (STestImpl test : getTests()) if (!test.isRemote()) return false;
		return true;
	}
	public boolean isModifiedRecursive() {
		if (isModified()) return true;
		for (STestImpl test : getTests()) if (test.isModified()) return true;
		return false;
	}
	
	private STestSuiteImpl() {}
	
	private void createTestList(Iterable<STestSnap> source) throws SException {
		List<STestImpl> tests = new ArrayList<STestImpl>();
		for (STestSnap snap : source) tests.add(STestImpl.create(snap, problem));
		this.tests = tests;
	}
	
	public static STestSuiteImpl create(STestSuiteSnap snap, SParentProblem problem) throws SException {
		if (!snap.isComplete()) snap.reload();
		STestSuiteImpl self = new STestSuiteImpl();
		self.snap = snap;
		self.snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.problem = problem;
		self.name = snap.getName();
		self.desc = snap.getDescription();
		self.createTestList(snap.getTests());
		return self;
	}
	public static STestSuiteImpl createNew(SParentProblem problem) {
		STestSuiteImpl self = new STestSuiteImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.desc = "";
		self.tests = new ArrayList<STestImpl>();
		return self;
	}
	public static STestSuiteImpl createNew(Iterable<STestSnap> tests, SParentProblem problem) throws SException {
		STestSuiteImpl self = new STestSuiteImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.desc = "";
		self.createTestList(tests);
		return self;
	}
	public static STestSuiteImpl createNew(STestImpl test, SParentProblem problem) {
		STestSuiteImpl self = new STestSuiteImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.desc = "";
		self.tests = new ArrayList<STestImpl>();
		self.tests.add(test);
		return self;
	}
	
	private boolean checkTestLists(Iterable<? extends STestBasicReader> list1) {
		Iterator<? extends STestBasicReader> iter1 = list1.iterator();
		Iterator<STestImpl> iter2 = tests.iterator();
		while (iter1.hasNext() && iter2.hasNext()) {
			STestImpl test = iter2.next();
			if (!test.isRemote() || test.getId() != iter1.next().getId()) return true;
		}
		if (iter1.hasNext() || iter2.hasNext()) return true;
		return false;
	}
	private boolean check(STestSuiteReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test suite ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (!source.getDescription().equals(desc)) return true;
		if (checkTestLists(source.getTests())) return true;
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
	public void setDescription(String desc) {
		if (this.desc.equals(desc)) return;
		this.desc = desc;
		notifyModified();
	}
	
	public STestImpl getTest(long id) {
		for (STestImpl test : tests) if (test.isRemote() && test.getId() == id) return test;
		return null;
	}
	public boolean hasTest(long id) { return getTest(id) != null; }
	public void addTest(STestImpl test) {
		SAssert.assertFalse(tests.contains(test), "Test already contained");
		tests.add(test);
		notifyModified();
	}
	public void addTest(STestImpl test, int index) {
		SAssert.assertFalse(tests.contains(test), "Test already contained");
		tests.add(index, test);
		notifyModified();
	}
	public void removeTest(STestImpl test) {
		SAssert.assertTrue(tests.contains(test), "Removing uncontained test");
		tests.remove(test);
		notifyModified();
	}
	public void moveTest(STestImpl test, int index) {
		SAssert.assertTrue(tests.contains(test), "Moving uncontained test");
		int old_index = tests.indexOf(test);
		if (index == old_index || index == old_index+1) return;
		tests.remove(test);
		if (old_index < index) --index;
		tests.add(index, test);
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
	
	public void setPane(SList<STestImpl> pane) { this.pane = pane; }
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void reload() throws SException {
		SAssert.assertTrue(isRemote(), "Test suite not remote");
		snap.reload(); //calls snapModified
		pane.removeAll();
		for (STestImpl test : tests) test.close();
		name = snap.getName();
		desc = snap.getDescription();
		createTestList(snap.getTests());
		pane.add(tests);
		notifyUpToDate();
	}
	public void create() throws SException {
		SAssert.assertFalse(isRemote(), "Test suite already created");
		id.set(STestSuiteData.create(this));
		notifyUpToDate();
		snap = STestSuiteSnap.create(problem.getTestList(), this);
		snap.addReference(reference);
		problem.getTestSuiteList().addTestSuite(snap);
	}
	public void save() throws SException {
		SAssert.assertTrue(isRemote(), "Test suite not remote");
		STestSuiteData.save(this);
		notifyUpToDate();
		snap.set(this);
	}
	public void delete() throws SException {
		SAssert.assertTrue(isRemote(), "Test suite not remote");
		STestSuiteData.delete(getId());
		problem.getTestSuiteList().removeTestSuite(snap);
		snap.notifyDeleted(); //calls snapDeleted
	}
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		snap = null;
	}
}
