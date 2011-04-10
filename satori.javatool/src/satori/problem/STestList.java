package satori.problem;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.common.SException;
import satori.common.SListView;
import satori.test.STestBasicReader;
import satori.test.STestSnap;
import satori.thrift.STestData;

public class STestList {
	private final long problem_id;
	
	private Map<Long, STestSnap> tests = null;
	private List<SListView<STestSnap>> panes = new ArrayList<SListView<STestSnap>>();
	
	public long getProblemId() { return problem_id; }
	
	private STestList(long problem_id) { this.problem_id = problem_id; }
	
	/*public static STestList createRemote(long problem_id) throws SException {
		STestList self = new STestList(problem_id);
		self.reload();
		return self;
	}*/
	public static STestList createNew(long problem_id) {
		STestList self = new STestList(problem_id);
		self.tests = new HashMap<Long, STestSnap>();
		return self;
	}
	
	public void addTest(STestSnap test) {
		tests.put(test.getId(), test);
		for (SListView<STestSnap> pane : panes) pane.add(test);
	}
	public void removeTest(STestSnap test) {
		for (SListView<STestSnap> pane : panes) pane.remove(test);
		tests.remove(test.getId());
	}
	
	//used by STestSuiteSnap
	public STestSnap getTest(STestBasicReader test) {
		if (tests.containsKey(test.getId())) return tests.get(test.getId());
		STestSnap result = STestSnap.createBasic(test);
		addTest(result);
		return result;
	}
	
	public void addPane(SListView<STestSnap> pane) {
		panes.add(pane);
		pane.add(tests.values());
	}
	public void removePane(SListView<STestSnap> pane) {
		pane.removeAll();
		panes.remove(pane);
	}
	
	public void reload() throws SException {
		Map<Long, STestSnap> new_tests = new HashMap<Long, STestSnap>();
		for (STestBasicReader t : STestData.list(problem_id)) {
			STestSnap current = tests != null ? tests.get(t.getId()) : null;
			if (current != null) current.setBasic(t);
			else current = STestSnap.createBasic(t);
			new_tests.put(current.getId(), current);
		}
		for (SListView<STestSnap> pane : panes) pane.removeAll();
		if (tests != null) for (long id : tests.keySet()) {
			if (!new_tests.containsKey(id)) tests.get(id).notifyDeleted();
		}
		tests = new_tests;
		for (SListView<STestSnap> pane : panes) pane.add(tests.values());
	}
	public void delete() {
		for (SListView<STestSnap> pane : panes) pane.removeAll();
		for (STestSnap t : tests.values()) t.notifyDeleted();
	}
}
