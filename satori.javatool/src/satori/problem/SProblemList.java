package satori.problem;

import java.util.HashMap;
import java.util.Map;

import satori.common.SException;
import satori.common.SList;
import satori.thrift.SProblemData;

public class SProblemList {
	private Map<Long, SProblemSnap> problems = null;
	private SList<SProblemSnap> pane = null;
	
	private SProblemList() {}
	
	public void addProblem(SProblemSnap problem) {
		problems.put(problem.getId(), problem);
		if (pane != null) pane.add(problem);
	}
	public void removeProblem(SProblemSnap problem) {
		if (pane != null) pane.remove(problem);
		problems.remove(problem.getId());
	}
	
	public boolean hasPane() { return pane != null; }
	public void setPane(SList<SProblemSnap> new_pane) {
		if (pane != null) pane.removeAll();
		pane = new_pane;
		if (pane != null) pane.add(problems.values());
	}
	
	public void load() throws SException {
		Map<Long, SProblemSnap> new_problems = new HashMap<Long, SProblemSnap>();
		for (SProblemReader problem : SProblemData.list()) {
			SProblemSnap current = problems != null ? problems.get(problem.getId()) : null;
			if (current != null) current.set(problem);
			else current = SProblemSnap.create(problem);
			new_problems.put(current.getId(), current);
		}
		if (pane != null) pane.removeAll();
		if (problems != null) for (Map.Entry<Long, SProblemSnap> entry : problems.entrySet()) {
			if (!new_problems.containsKey(entry.getKey())) entry.getValue().notifyDeleted();
		}
		problems = new_problems;
		if (pane != null) pane.add(problems.values());
	}
	
	private static SProblemList instance = null;
	
	public static SProblemList get() throws SException {
		if (instance == null) instance = new SProblemList();
		instance.load();
		return instance;
	}
}
