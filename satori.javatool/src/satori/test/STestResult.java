package satori.test;

import satori.common.SException;
import satori.common.SId;
import satori.common.SListener0;
import satori.common.SView;
import satori.common.SViewList;
import satori.server.STemporarySubmitData;

public class STestResult {
	public static enum Status { NOT_TESTED, PENDING, FINISHED };
	
	private SId id = new SId();
	private final SSolution solution;
	private final STestImpl test;
	
	private Status status = Status.NOT_TESTED;
	private String message = null;
	
	private final SViewList views = new SViewList();
	private final SListener0 clear_listener = new SListener0() {
		@Override public void call() { clear(); }
	};
	
	public STestResult(SSolution solution, STestImpl test) {
		this.solution = solution;
		this.test = test;
		solution.addModifiedListener(clear_listener);
		test.addDataModifiedListener(clear_listener);
	}
	
	public Status getStatus() { return status; }
	public String getMessage() { return message; }
	
	private void clear() {
		id.clear();
		status = Status.NOT_TESTED;
		message = null;
		updateViews();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void run() throws SException {
		if (solution.get() == null) return;
		id.set(STemporarySubmitData.create(solution.get(), test.getData()));
		status = Status.PENDING;
		message = null;
		updateViews();
	}
	public void refresh() throws SException {
		if (!id.isSet()) return;
		STemporarySubmitReader source = STemporarySubmitData.load(id.get());
		if (source.getPending()) {
			status = Status.PENDING;
			message = null;
		} else {
			status = Status.FINISHED;
			message = source.getResult().getString("status");
		}
		updateViews();
	}
	public void close() {
		test.removeDataModifiedListener(clear_listener);
		solution.removeModifiedListener(clear_listener);
	}
}
