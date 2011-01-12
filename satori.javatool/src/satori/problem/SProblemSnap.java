package satori.problem;

import satori.common.SException;
import satori.common.SReference;
import satori.common.SReferenceList;
import satori.common.SView;
import satori.common.SViewList;

public class SProblemSnap implements SProblemReader {
	private long id;
	private String name;
	private String desc;
	//private Map<Long, STestSnap> tests;
	//private Map<Long, STestSuiteSnap> suites;
	
	private STestList test_list = null;
	private STestSuiteList suite_list = null;
	
	private final SViewList views = new SViewList();
	private final SReferenceList refs = new SReferenceList();
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	
	public STestList getTestList() { return test_list; }
	public STestSuiteList getTestSuiteList() { return suite_list; }
	
	private SProblemSnap() {}
	
	public static SProblemSnap create(SProblemReader source) {
		SProblemSnap self = new SProblemSnap();
		self.id = source.getId();
		self.name = source.getName();
		self.desc = source.getDescription();
		//self.tests = null;
		//self.suites = null;
		return self;
	}
	/*public static SProblemSnap createNew(SProblemReader source) {
		SProblemSnap self = new SProblemSnap();
		self.id = source.getId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.tests = new HashMap<Long, STestSnap>();
		self.suites = new HashMap<Long, STestSuiteSnap>();
		return self;
	}*/
	
	private void setBasic(SProblemReader source) {
		if (source.getId() != getId()) throw new RuntimeException("Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
	}
	/*private void setTests(Iterable<STestBasicReader> source) {
		Map<Long, STestSnap> new_tests = new HashMap<Long, STestSnap>();
		for (STestBasicReader test : source) {
			STestSnap current = tests != null ? tests.get(test.getId()) : null;
			if (current != null) current.setBasic(test);
			else current = STestSnap.createBasic(test);
			new_tests.put(current.getId(), current);
		}
		if (tests != null) for (long id : tests.keySet()) {
			if (!new_tests.containsKey(id)) tests.get(id).notifyDeleted();
		}
		tests = new_tests;
	}
	private void setTestSuites(Iterable<STestSuiteBasicReader> source) {
		Map<Long, STestSuiteSnap> new_suites = new HashMap<Long, STestSuiteSnap>();
		for (STestSuiteBasicReader suite : source) {
			STestSuiteSnap current = suites != null ? suites.get(suite.getId()) : null;
			if (current != null) current.setBasic(suite);
			else current = STestSuiteSnap.createBasic(test_list, suite);
			new_suites.put(current.getId(), current);
		}
		if (suites != null) for (long id : suites.keySet()) {
			if (!new_suites.containsKey(id)) suites.get(id).notifyDeleted();
		}
		suites = new_suites;
	}*/
	
	public void set(SProblemReader source) {
		setBasic(source);
		notifyModified();
	}
	/*public void reload() throws SException {
		setBasic(SProblemData.load(id));
		setTests(STestData.list(id));
		setTestSuites(STestSuiteData.list(id));
		notifyModified();
	}*/
	
	/*public void addTest(STestSnap test) {
		if (tests.containsKey(test.getId())) throw new RuntimeException("Test already contained");
		tests.put(test.getId(), test);
		notifyModified();
	}
	public void removeTest(STestSnap test) {
		if (tests.get(test.getId()) != test) throw new RuntimeException("Removing uncontained test");
		tests.remove(test.getId());
		notifyModified();
	}*/
	
	private void notifyModified() {
		updateViews();
		refs.notifyModified();
	}
	public void notifyDeleted() {
		refs.notifyDeleted();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void setTestList(STestList test_list) {
		if (this.test_list != null) throw new RuntimeException("Multiple test list");
		this.test_list = test_list;
	}
	public void setTestSuiteList(STestSuiteList suite_list) {
		if (this.suite_list != null) throw new RuntimeException("Multiple test suite list");
		this.suite_list = suite_list;
	}
	
	public void addReference(SReference ref) throws SException {
		if (test_list == null) test_list = STestList.createRemote(id);
		if (suite_list == null) suite_list = STestSuiteList.createRemote(id, test_list);
		refs.add(ref);
	}
	public void removeReference(SReference ref) {
		refs.remove(ref);
		if (refs.isEmpty()) {
			test_list = null;
			suite_list = null;
		}
	}
}
