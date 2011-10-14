package satori.test.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SId;
import satori.common.SListener0;
import satori.common.SReference;
import satori.common.SView;
import satori.data.SBlob;
import satori.data.STestData;
import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;
import satori.metadata.SJudgeParser;
import satori.problem.SParentProblem;
import satori.task.SResultTask;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskHandler;
import satori.test.STestReader;
import satori.test.STestSnap;

public class STestImpl implements STestReader {
	private final SParentProblem problem;
	
	private STestSnap snap = null;
	private SId id = SId.unset();
	private String name = "";
	private String desc = "";
	private SJudge judge = null;
	private Map<SInputMetadata, Object> input = Collections.emptyMap();
	
	private final SDataStatus status = new SDataStatus();
	private final List<SListener0> data_modified_listeners = new ArrayList<SListener0>();
	private final List<SListener0> metadata_modified_listeners = new ArrayList<SListener0>();
	private final List<SView> views = new ArrayList<SView>();
	private final SReference reference = new SReference() {
		@Override public void notifyModified() { snapModified(); }
		@Override public void notifyDeleted() { snapDeleted(); }
	};
	
	@Override public boolean hasId() { return id.isSet(); }
	@Override public long getId() { return id.get(); }
	@Override public long getProblemId() { return problem.getId(); }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	@Override public SJudge getJudge() { return judge; }
	@Override public Map<SInputMetadata, Object> getInput() { return Collections.unmodifiableMap(input); }
	public Object getInput(SInputMetadata meta) { return input.get(meta); }
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	public boolean isProblemRemote() { return problem.hasId(); }
	
	private STestImpl(SParentProblem problem) {
		this.problem = problem;
	}
	
	public static STestImpl createNew(SParentProblem problem) {
		return new STestImpl(problem);
	}
	public static STestImpl createRemote(STaskHandler handler, SParentProblem problem, STestSnap snap) throws STaskException {
		STestImpl self = new STestImpl(problem);
		self.snap = snap;
		self.snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.reload(handler);
		return self;
	}
	
	private boolean check(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (!source.getDescription().equals(desc)) return true;
		if (source.getJudge() == null && judge != null) return true;
		if (source.getJudge() != null && !source.getJudge().equals(judge)) return true;
		if (!input.equals(source.getInput())) return true;
		return false;
	}
	
	private void snapModified() {
		if (!check(snap)) return;
		notifyOutdated();
	}
	private void snapDeleted() {
		snap = null;
		id = SId.unset();
		notifyOutdated();
	}
	
	public void setName(String name) {
		if (this.name.equals(name)) return;
		this.name = name;
		notifyModified();
	}
	public void setDescription(String desc) {
		if (this.desc.equals(desc)) return;
		this.desc = desc;
		notifyModified();
	}
	private static SInputMetadata getInputMetadataByName(List<SInputMetadata> list, String name) {
		for (SInputMetadata meta : list) if (meta.getName().equals(name)) return meta;
		return null;
	}
	public void setJudge(STaskHandler handler, SBlob blob) throws STaskException {
		if (blob == null && judge == null) return;
		if (blob != null && judge != null && blob.equals(judge.getBlob())) return;
		if (blob != null) {
			List<SInputMetadata> old_input_meta = judge != null ? judge.getInputMetadata() : null;
			Map<SInputMetadata, Object> old_input = input;
			judge = SJudgeParser.parseJudge(handler, blob);
			input = new HashMap<SInputMetadata, Object>();
			for (SInputMetadata meta : judge.getInputMetadata()) {
				SInputMetadata old_meta = old_input_meta != null ? getInputMetadataByName(old_input_meta, meta.getName()) : null;
				if (old_meta != null && old_meta.getType() != meta.getType()) old_meta = null;
				Object value = old_meta != null ? old_input.get(old_meta) : null;
				if (value == null) value = meta.getDefaultValue();
				if (value != null) input.put(meta, value);
			}
		} else {
			judge = null;
			input = Collections.emptyMap();
		}
		notifyModified();
		callMetadataModifiedListeners();
		callDataModifiedListeners();
	}
	public void setInput(SInputMetadata meta, Object value) {
		Object old_value = input.get(meta);
		if (value == null && old_value == null) return;
		if (value != null && value.equals(old_value)) return;
		if (value != null) input.put(meta, value);
		else input.remove(meta);
		notifyModified();
		callDataModifiedListeners();
	}
	
	private void notifyModified() {
		status.markModified();
		updateViews();
	}
	private void notifyOutdated() {
		status.markOutdated();
		updateViews();
	}
	private void notifyUpToDate() {
		status.markUpToDate();
		updateViews();
	}
	
	public void addDataModifiedListener(SListener0 listener) { data_modified_listeners.add(listener); }
	public void removeDataModifiedListener(SListener0 listener) { data_modified_listeners.remove(listener); }
	private void callDataModifiedListeners() { for (SListener0 listener : data_modified_listeners) listener.call(); }
	
	public void addMetadataModifiedListener(SListener0 listener) { metadata_modified_listeners.add(listener); }
	public void removeMetadataModifiedListener(SListener0 listener) { metadata_modified_listeners.remove(listener); }
	private void callMetadataModifiedListeners() { for (SListener0 listener : metadata_modified_listeners) listener.call(); }
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
	
	public void reload(final STaskHandler handler) throws STaskException {
		STestReader source = handler.execute(new SResultTask<STestReader>() {
			@Override public STestReader run() throws Exception {
				return STestData.load(handler, getId());
			}
		});
		name = source.getName();
		judge = source.getJudge();
		desc = source.getDescription();
		input = new HashMap<SInputMetadata, Object>(source.getInput());
		notifyUpToDate();
		callMetadataModifiedListeners();
		callDataModifiedListeners();
		snap.set(this);
	}
	public void create(final STaskHandler handler) throws STaskException {
		id = handler.execute(new SResultTask<SId>() {
			@Override public SId run() throws Exception {
				return new SId(STestData.create(handler, STestImpl.this));
			}
		});
		notifyUpToDate();
		snap = STestSnap.create(this);
		snap.addReference(reference);
		problem.getTestList().addTest(snap);
	}
	public void save(final STaskHandler handler) throws STaskException {
		handler.execute(new STask() {
			@Override public void run() throws Exception {
				STestData.save(handler, STestImpl.this);
			}
		});
		notifyUpToDate();
		snap.set(this);
	}
	public void delete(final STaskHandler handler) throws STaskException {
		handler.execute(new STask() {
			@Override public void run() throws Exception {
				STestData.delete(handler, getId());
			}
		});
		problem.getTestList().removeTest(snap);
		snap.notifyDeleted(); //calls snapDeleted
	}
	
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		snap = null;
	}
}
