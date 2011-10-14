package satori.test.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import satori.common.SId;
import satori.common.SListener0;
import satori.common.SView;
import satori.data.STemporarySubmitData;
import satori.metadata.SOutputMetadata;
import satori.task.SResultTask;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskHandler;
import satori.test.STemporarySubmitReader;

public class STestResult {
	public static enum Status { NOT_TESTED, PENDING, FINISHED };
	
	private SId id = SId.unset();
	private final SSolution solution;
	private final STestImpl test;
	
	private Status status = Status.NOT_TESTED;
	private Map<SOutputMetadata, Object> output = Collections.emptyMap();
	
	private final List<SView> views = new ArrayList<SView>();
	private final SListener0 clear_listener = new SListener0() {
		@Override public void call() { clear(); }
	};
	
	public STestResult(SSolution solution, STestImpl test) {
		this.solution = solution;
		this.test = test;
		solution.addModifiedListener(clear_listener);
		test.addDataModifiedListener(clear_listener);
	}
	
	public STestImpl getTest() { return test; }
	public Status getStatus() { return status; }
	public Object getOutput(SOutputMetadata meta) { return output.get(meta); }
	
	private void clear() {
		id = SId.unset();
		status = Status.NOT_TESTED;
		output = Collections.emptyMap();
		updateViews();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
	
	public void run(final STaskHandler handler) throws STaskException {
		if (solution.get() == null) return;
		if (test.getJudge() == null) return;
		handler.execute(new STask() {
			@Override public void run() throws Exception {
				id = new SId(STemporarySubmitData.create(handler, solution.get(), test));
			}
		});
		status = Status.PENDING;
		output = Collections.emptyMap();
		updateViews();
	}
	
	public void refresh(final STaskHandler handler) throws STaskException {
		if (!id.isSet()) return;
		STemporarySubmitReader submit = handler.execute(new SResultTask<STemporarySubmitReader>() {
			@Override public STemporarySubmitReader run() throws Exception {
				return STemporarySubmitData.load(handler, id.get(), test.getJudge().getOutputMetadata());
			}
		});
		if (submit.getPending()) {
			status = Status.PENDING;
			output = Collections.emptyMap();
		} else {
			status = Status.FINISHED;
			output = submit.getResult();
		}
		updateViews();
	}
	
	public void close() {
		test.removeDataModifiedListener(clear_listener);
		solution.removeModifiedListener(clear_listener);
	}
}
