package satori.problem;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.common.SException;
import satori.common.SList;
import satori.thrift.STestSuiteData;

public class STestSuiteList {
	private final long problem_id;
	private final STestList test_list;
	
	private Map<Long, STestSuiteSnap> suites = null;
	private List<SList<STestSuiteSnap>> panes = new ArrayList<SList<STestSuiteSnap>>();
	
	public long getProblemId() { return problem_id; }
	public STestList getTestList() { return test_list; }
	
	private STestSuiteList(long problem_id, STestList test_list) {
		this.problem_id = problem_id;
		this.test_list = test_list;
	}
	
	public static STestSuiteList createRemote(long problem_id, STestList test_list) throws SException {
		STestSuiteList self = new STestSuiteList(problem_id, test_list);
		self.reload();
		return self;
	}
	public static STestSuiteList createNew(long problem_id, STestList test_list) {
		STestSuiteList self = new STestSuiteList(problem_id, test_list);
		self.suites = new HashMap<Long, STestSuiteSnap>();
		return self;
	}
	
	public void addTestSuite(STestSuiteSnap suite) {
		suites.put(suite.getId(), suite);
		for (SList<STestSuiteSnap> pane : panes) pane.add(suite);
	}
	public void removeTestSuite(STestSuiteSnap suite) {
		for (SList<STestSuiteSnap> pane : panes) pane.remove(suite);
		suites.remove(suite.getId());
	}
	
	public void addPane(SList<STestSuiteSnap> pane) {
		panes.add(pane);
		pane.add(suites.values());
	}
	public void removePane(SList<STestSuiteSnap> pane) {
		pane.removeAll();
		panes.remove(pane);
	}
	
	public void reload() throws SException {
		Map<Long, STestSuiteSnap> new_suites = new HashMap<Long, STestSuiteSnap>();
		for (STestSuiteBasicReader ts : STestSuiteData.list(problem_id)) {
			STestSuiteSnap current = suites != null ? suites.get(ts.getId()) : null;
			if (current != null) current.setBasic(ts);
			else current = STestSuiteSnap.createBasic(test_list, ts);
			new_suites.put(current.getId(), current);
		}
		for (SList<STestSuiteSnap> pane : panes) pane.removeAll();
		if (suites != null) for (long id : suites.keySet()) {
			if (!new_suites.containsKey(id)) suites.get(id).notifyDeleted();
		}
		suites = new_suites;
		for (SList<STestSuiteSnap> pane : panes) pane.add(suites.values());
	}
	public void delete() {
		for (SList<STestSuiteSnap> pane : panes) pane.removeAll();
		for (STestSuiteSnap ts : suites.values()) ts.notifyDeleted();
	}
}
