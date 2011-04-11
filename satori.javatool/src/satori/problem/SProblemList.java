package satori.problem;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.common.SListView;
import satori.data.SProblemData;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskManager;

public class SProblemList {
	private Map<Long, SProblemSnap> problems = null;
	private SListView<SProblemSnap> pane = null;
	
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
	public void setPane(SListView<SProblemSnap> new_pane) {
		if (pane != null) pane.removeAll();
		pane = new_pane;
		if (pane != null) pane.add(problems.values());
	}
	
	private class LoadTask implements STask {
		public List<SProblemReader> problems;
		@Override public void run() throws Exception {
			problems = SProblemData.list();
		}
	}
	public void reload() throws STaskException {
		LoadTask task = new LoadTask();
		STaskManager.execute(task);
		Map<Long, SProblemSnap> new_problems = new HashMap<Long, SProblemSnap>();
		for (SProblemReader problem : task.problems) {
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
	
	public static SProblemList get() throws STaskException {
		if (instance == null) instance = new SProblemList();
		instance.reload();
		return instance;
	}
}
