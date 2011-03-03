package satori.test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import satori.blob.SBlob;
import satori.common.SAssert;
import satori.common.SException;
import satori.common.SListener1;
import satori.common.SReference;
import satori.common.SView;
import satori.metadata.SInputMetadata;
import satori.metadata.SOutputMetadata;
import satori.thrift.STestData;

public class STestSnap implements STestReader {
	private long id;
	private long problem_id;
	private String name;
	private SBlob judge;
	private List<SInputMetadata> input_meta;
	private List<SOutputMetadata> output_meta;
	private Map<SInputMetadata, Object> input;
	private boolean complete;
	
	private final List<SView> views = new ArrayList<SView>();
	private final List<SReference> refs = new ArrayList<SReference>();
	private final List<SListener1<STestSnap>> deleted_listeners = new ArrayList<SListener1<STestSnap>>();
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public long getProblemId() { return problem_id; }
	@Override public String getName() { return name; }
	@Override public SBlob getJudge() { return judge; }
	@Override public List<SInputMetadata> getInputMetadata() { return input_meta; }
	@Override public List<SOutputMetadata> getOutputMetadata() { return output_meta; }
	@Override public Map<SInputMetadata, Object> getInput() { return Collections.unmodifiableMap(input); }
	
	public boolean isComplete() { return complete; }
	
	private STestSnap() {}
	
	public static STestSnap create(STestReader source) {
		STestSnap self = new STestSnap();
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.judge = source.getJudge();
		self.input_meta = source.getInputMetadata();
		self.output_meta = source.getOutputMetadata();
		self.input = source.getInput();
		self.complete = true;
		return self;
	}
	public static STestSnap createBasic(STestBasicReader source) {
		STestSnap self = new STestSnap();
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.complete = false;
		return self;
	}
	
	public void set(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		judge = source.getJudge();
		input_meta = source.getInputMetadata();
		output_meta = source.getOutputMetadata();
		input = source.getInput();
		complete = true;
		notifyModified();
	}
	public void setBasic(STestBasicReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		notifyModified();
	}
	public void reload() throws SException { set(STestData.load(id)); }
	
	private void notifyModified() {
		for (SView view : views) view.update();
		for (SReference ref : refs) ref.notifyModified();
	}
	public void notifyDeleted() {
		for (SListener1<STestSnap> listener : deleted_listeners) listener.call(this);
		for (SReference ref : refs) ref.notifyDeleted();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	
	public void addDeletedListener(SListener1<STestSnap> listener) { deleted_listeners.add(listener); }
	public void removeDeletedListener(SListener1<STestSnap> listener) { deleted_listeners.remove(listener); }
	
	public void addReference(SReference ref) { refs.add(ref); }
	public void removeReference(SReference ref) { refs.remove(ref); }
}
