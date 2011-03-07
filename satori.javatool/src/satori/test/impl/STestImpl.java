package satori.test.impl;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SException;
import satori.common.SId;
import satori.common.SListener0;
import satori.common.SReference;
import satori.common.SView;
import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;
import satori.metadata.SJudgeParser;
import satori.problem.SParentProblem;
import satori.test.STestReader;
import satori.test.STestSnap;
import satori.thrift.STestData;

public class STestImpl implements STestReader {
	private STestSnap snap = null;
	private SId id;
	private SParentProblem problem;
	private String name;
	private SJudge judge;
	private Map<SInputMetadata, Object> input;
	
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
	@Override public SJudge getJudge() { return judge; }
	@Override public Map<SInputMetadata, Object> getInput() { return Collections.unmodifiableMap(input); }
	public Object getInput(SInputMetadata meta) { return input.get(meta); }
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	public boolean isProblemRemote() { return problem.hasId(); }
	
	private STestImpl() {}
	
	public static STestImpl create(STestSnap snap, SParentProblem problem) throws SException {
		if (!snap.isComplete()) snap.reload();
		STestImpl self = new STestImpl();
		self.snap = snap;
		self.snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.problem = problem;
		self.name = snap.getName();
		self.judge = snap.getJudge();
		self.input = new HashMap<SInputMetadata, Object>(snap.getInput());
		return self;
	}
	public static STestImpl createNew(SParentProblem problem) {
		STestImpl self = new STestImpl();
		self.id = new SId();
		self.problem = problem;
		self.name = "";
		self.judge = null;
		self.input = Collections.emptyMap();
		return self;
	}
	
	private boolean check(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
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
		id.clear();
		notifyOutdated();
	}
	
	public void setName(String name) {
		if (this.name.equals(name)) return;
		this.name = name;
		notifyModified();
	}
	public void setJudge(SBlob blob) throws SException {
		if (blob == null && judge == null) return;
		if (blob != null && judge != null && blob.equals(judge.getBlob())) return;
		if (blob != null) {
			judge = SJudgeParser.parseJudge(blob);
			input = new HashMap<SInputMetadata, Object>();
			for (SInputMetadata meta : judge.getInputMetadata()) {
				Object def_value = meta.getDefaultValue();
				if (def_value != null) input.put(meta, def_value);
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
	
	public void reload() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		snap.reload();
		name = snap.getName();
		judge = snap.getJudge();
		input = new HashMap<SInputMetadata, Object>(snap.getInput());
		notifyUpToDate();
		callDataModifiedListeners();
	}
	public void create() throws SException {
		SAssert.assertFalse(isRemote(), "Test already created");
		id.set(STestData.create(this));
		notifyUpToDate();
		snap = STestSnap.create(this);
		snap.addReference(reference);
		problem.getTestList().addTest(snap);
	}
	public void save() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		STestData.save(this);
		notifyUpToDate();
		snap.set(this);
	}
	public void delete() throws SException {
		SAssert.assertTrue(isRemote(), "Test not remote");
		STestData.delete(getId());
		problem.getTestList().removeTest(snap);
		snap.notifyDeleted(); //calls snapDeleted
	}
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		snap = null;
	}
}
