package satori.test.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import satori.common.SAssert;
import satori.common.SListener0;
import satori.problem.SParentProblem;
import satori.task.STaskException;
import satori.test.STestSnap;

public class STestSuiteBase {
	public interface View {
		void add(STestImpl test, int index);
		void add(Iterable<STestImpl> tests, int index);
		void remove(STestImpl test, int index);
		void removeAll();
		void move(STestImpl test, int old_index, int new_index);
	};
	
	private List<STestImpl> tests;
	private View list_view = null;
	private SListener0 modified_listener = null;
	
	public List<STestImpl> getTests() { return Collections.unmodifiableList(tests); }
	public int getSize() { return tests.size(); }
	
	private STestSuiteBase() {}
	
	public static List<STestImpl> createTestList(SParentProblem problem, List<STestSnap> source) throws STaskException {
		List<STestImpl> tests = new ArrayList<STestImpl>();
		for (STestSnap snap : source) tests.add(STestImpl.createRemote(problem, snap));
		return tests;
	}
	public static STestSuiteBase create(SParentProblem problem, List<STestSnap> source) throws STaskException {
		STestSuiteBase self = new STestSuiteBase();
		self.tests = createTestList(problem, source);
		return self;
	}
	public static STestSuiteBase createNew() {
		STestSuiteBase self = new STestSuiteBase();
		self.tests = new ArrayList<STestImpl>();
		return self;
	}
	public static STestSuiteBase createNew(List<STestImpl> tests) {
		STestSuiteBase self = new STestSuiteBase();
		self.tests = new ArrayList<STestImpl>(tests);
		return self;
	}
	
	public void setTestList(List<STestImpl> tests) {
		if (list_view != null) list_view.removeAll();
		tests = new ArrayList<STestImpl>(tests);
		if (list_view != null) list_view.add(tests, 0);
	}
	
	public void setListView(View list_view) {
		SAssert.assertNull(this.list_view, "List view already set");
		this.list_view = list_view;
		this.list_view.add(tests, 0);
	}
	public void setModifiedListener(SListener0 modified_listener) {
		SAssert.assertNull(this.modified_listener, "Modified listener already set");
		this.modified_listener = modified_listener;
	}
	
	public void addTest(STestImpl test, int index) {
		tests.add(index, test);
		if (list_view != null) list_view.add(test, index);
		if (modified_listener != null) modified_listener.call();
	}
	public void addTests(Iterable<STestImpl> tests, int index) {
		int cur_index = index;
		for (STestImpl test : tests) this.tests.add(cur_index++, test);
		if (list_view != null) list_view.add(tests, index);
		if (modified_listener != null) modified_listener.call();
	}
	public void removeTest(STestImpl test) {
		int index = tests.indexOf(test);
		tests.remove(index);
		if (list_view != null) list_view.remove(test, index);
		if (modified_listener != null) modified_listener.call();
	}
	public void moveTest(STestImpl test, int new_index) {
		int old_index = tests.indexOf(test);
		tests.remove(old_index);
		tests.add(old_index < new_index ? new_index-1 : new_index, test);
		if (list_view != null) list_view.move(test, old_index, new_index);
		if (modified_listener != null) modified_listener.call();
	}
	
	public boolean hasModifiedTests() {
		for (STestImpl test : tests) if (test.isModified()) return true;
		return false;
	}
	public void closeTests() {
		for (STestImpl test : tests) test.close();
	}
}
