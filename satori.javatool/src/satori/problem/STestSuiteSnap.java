package satori.problem;

import java.util.ArrayList;
import java.util.List;

import satori.common.SException;
import satori.common.SListener;
import satori.common.SReference;
import satori.common.SReferenceList;
import satori.common.SView;
import satori.common.SViewList;
import satori.server.STestSuiteData;
import satori.test.STestBasicReader;
import satori.test.STestSnap;

public class STestSuiteSnap implements STestSuiteReader {
	private final STestList test_list;
	
	private long id;
	private long problem_id;
	private String name;
	private String desc;
	private List<STestSnap> tests;
	
	private final SViewList views = new SViewList();
	private final SReferenceList refs = new SReferenceList();
	private final SListener<STestSnap> test_deleted_listener = new SListener<STestSnap>() {
		@Override public void call(STestSnap test) { testDeleted(test); }
	};
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public long getProblemId() { return problem_id; }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	@Override public Iterable<STestSnap> getTests() { return tests; }
	
	public boolean isComplete() { return tests != null; }
	
	private STestSuiteSnap(STestList test_list) {
		this.test_list = test_list;
	}
	
	private static List<STestSnap> createTestList(STestList test_list, Iterable<? extends STestBasicReader> source) {
		List<STestSnap> snaps = new ArrayList<STestSnap>();
		for (STestBasicReader test : source) snaps.add(test_list.getTestSnap(test.getId()));
		return snaps;
	}
	
	public static STestSuiteSnap create(STestList test_list, STestSuiteReader source) {
		if (source.getProblemId() != test_list.getProblemId()) throw new RuntimeException("Problem ids don't match");
		STestSuiteSnap self = new STestSuiteSnap(test_list);
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.tests = createTestList(test_list, source.getTests());
		for (STestSnap test : self.tests) test.addDeletedListener(self.test_deleted_listener);
		return self;
	}
	public static STestSuiteSnap createBasic(STestList test_list, STestSuiteBasicReader source) {
		if (source.getProblemId() != test_list.getProblemId()) throw new RuntimeException("Problem ids don't match");
		STestSuiteSnap self = new STestSuiteSnap(test_list);
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.tests = null;
		return self;
	}
	
	public void set(STestSuiteReader source) {
		if (source.getId() != getId()) throw new RuntimeException("Test suite ids don't match");
		if (source.getProblemId() != getProblemId()) throw new RuntimeException("Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
		if (tests != null) for (STestSnap test : tests) test.removeDeletedListener(test_deleted_listener);
		tests = createTestList(test_list, source.getTests());
		for (STestSnap test : tests) test.addDeletedListener(test_deleted_listener);
		notifyModified();
	}
	public void setBasic(STestSuiteBasicReader source) {
		if (source.getId() != getId()) throw new RuntimeException("Test suite ids don't match");
		if (source.getProblemId() != getProblemId()) throw new RuntimeException("Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
		notifyModified();
	}
	public void reload() throws SException { set(STestSuiteData.load(id)); }
	
	private void testDeleted(STestSnap test) {
		tests.remove(test);
		//updateViews(); //TODO: is this necessary?
		refs.notifyModified();
	}
	
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
	
	public void addReference(SReference ref) { refs.add(ref); }
	public void removeReference(SReference ref) { refs.remove(ref); }
}
