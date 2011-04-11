package satori.problem;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import satori.common.SAssert;
import satori.common.SListener1;
import satori.common.SModel;
import satori.common.SPair;
import satori.common.SReference;
import satori.common.SView;
import satori.data.STestSuiteData;
import satori.metadata.SInputMetadata;
import satori.metadata.SParametersMetadata;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskManager;
import satori.test.STestBasicReader;
import satori.test.STestSnap;

public class STestSuiteSnap implements STestSuiteReader, SModel {
	private final STestList test_list;
	
	private long id;
	private long problem_id;
	private String name;
	private String desc;
	private List<STestSnap> tests;
	private SParametersMetadata dispatcher;
	private List<SParametersMetadata> accumulators;
	private SParametersMetadata reporter;
	private Map<SInputMetadata, Object> general_params;
	private Map<SPair<SInputMetadata, Long>, Object> test_params;
	
	private final List<SView> views = new ArrayList<SView>();
	private final List<SReference> refs = new ArrayList<SReference>();
	private final SListener1<STestSnap> test_deleted_listener = new SListener1<STestSnap>() {
		@Override public void call(STestSnap test) { testDeleted(test); }
	};
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public long getProblemId() { return problem_id; }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	@Override public List<STestSnap> getTests() { return Collections.unmodifiableList(tests); }
	@Override public SParametersMetadata getDispatcher() { return dispatcher; }
	@Override public List<SParametersMetadata> getAccumulators() { return accumulators; }
	@Override public SParametersMetadata getReporter() { return reporter; }
	@Override public Map<SInputMetadata, Object> getGeneralParameters() { return general_params; }
	@Override public Map<SPair<SInputMetadata, Long>, Object> getTestParameters() { return test_params; }
	
	public boolean isComplete() { return tests != null; }
	
	private STestSuiteSnap(STestList test_list) {
		this.test_list = test_list;
	}
	
	private void createTestList(List<? extends STestBasicReader> source) {
		tests = new ArrayList<STestSnap>();
		for (STestBasicReader test : source) tests.add(test_list.getTest(test));
	}
	private void addTestDeletedListeners() {
		for (STestSnap test : tests) test.addDeletedListener(test_deleted_listener);
	}
	private void removeTestDeletedListeners() {
		for (STestSnap test : tests) test.removeDeletedListener(test_deleted_listener);
	}
	
	public static STestSuiteSnap create(STestList test_list, STestSuiteReader source) {
		SAssert.assertEquals(source.getProblemId(), test_list.getProblemId(), "Problem ids don't match");
		STestSuiteSnap self = new STestSuiteSnap(test_list);
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.createTestList(source.getTests());
		self.addTestDeletedListeners();
		self.dispatcher = source.getDispatcher();
		self.accumulators = source.getAccumulators();
		self.reporter = source.getReporter();
		self.general_params = source.getGeneralParameters();
		self.test_params = source.getTestParameters();
		return self;
	}
	public static STestSuiteSnap createBasic(STestList test_list, STestSuiteBasicReader source) {
		SAssert.assertEquals(source.getProblemId(), test_list.getProblemId(), "Problem ids don't match");
		STestSuiteSnap self = new STestSuiteSnap(test_list);
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.tests = null;
		self.dispatcher = null;
		self.accumulators = null;
		self.reporter = null;
		self.general_params = null;
		self.test_params = null;
		return self;
	}
	
	public void set(STestSuiteReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test suite ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
		if (tests != null) removeTestDeletedListeners();
		createTestList(source.getTests());
		addTestDeletedListeners();
		dispatcher = source.getDispatcher();
		accumulators = source.getAccumulators();
		reporter = source.getReporter();
		general_params = source.getGeneralParameters();
		test_params = source.getTestParameters();
		notifyModified();
	}
	public void setBasic(STestSuiteBasicReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test suite ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
		notifyModified();
	}
	
	private class LoadTask implements STask {
		public STestSuiteReader suite;
		@Override public void run() throws Exception {
			suite = STestSuiteData.load(getId());
		}
	}
	public void reload() throws STaskException {
		LoadTask task = new LoadTask();
		STaskManager.execute(task);
		set(task.suite);
	}
	
	private void testDeleted(STestSnap test) {
		tests.remove(test);
		//for (SView view : views) view.update(); //TODO: is this necessary?
		for (SReference ref : refs) ref.notifyModified();
	}
	
	private void notifyModified() {
		for (SView view : views) view.update();
		for (SReference ref : refs) ref.notifyModified();
	}
	public void notifyDeleted() {
		for (SReference ref : refs) ref.notifyDeleted();
	}
	
	@Override public void addView(SView view) { views.add(view); }
	@Override public void removeView(SView view) { views.remove(view); }
	
	public void addReference(SReference ref) { refs.add(ref); }
	public void removeReference(SReference ref) { refs.remove(ref); }
}
