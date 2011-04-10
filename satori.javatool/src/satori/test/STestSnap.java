package satori.test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import satori.common.SAssert;
import satori.common.SException;
import satori.common.SListener1;
import satori.common.SModel;
import satori.common.SReference;
import satori.common.SView;
import satori.metadata.SInputMetadata;
import satori.metadata.SJudge;
import satori.thrift.STestData;

public class STestSnap implements STestReader, SModel {
	private long id;
	private long problem_id;
	private String name;
	private String desc;
	private SJudge judge;
	private Map<SInputMetadata, Object> input;
	private boolean complete;
	
	private final List<SView> views = new ArrayList<SView>();
	private final List<SReference> refs = new ArrayList<SReference>();
	private final List<SListener1<STestSnap>> deleted_listeners = new ArrayList<SListener1<STestSnap>>();
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public long getProblemId() { return problem_id; }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	@Override public SJudge getJudge() { return judge; }
	@Override public Map<SInputMetadata, Object> getInput() { return Collections.unmodifiableMap(input); }
	
	public boolean isComplete() { return complete; }
	
	private STestSnap() {}
	
	public static STestSnap create(STestReader source) {
		STestSnap self = new STestSnap();
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.judge = source.getJudge();
		self.input = source.getInput();
		self.complete = true;
		return self;
	}
	public static STestSnap createBasic(STestBasicReader source) {
		STestSnap self = new STestSnap();
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.desc = source.getDescription();
		self.complete = false;
		return self;
	}
	
	public void set(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
		judge = source.getJudge();
		input = source.getInput();
		complete = true;
		notifyModified();
	}
	public void setBasic(STestBasicReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
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
	
	@Override public void addView(SView view) { views.add(view); }
	@Override public void removeView(SView view) { views.remove(view); }
	
	public void addDeletedListener(SListener1<STestSnap> listener) { deleted_listeners.add(listener); }
	public void removeDeletedListener(SListener1<STestSnap> listener) { deleted_listeners.remove(listener); }
	
	public void addReference(SReference ref) { refs.add(ref); }
	public void removeReference(SReference ref) { refs.remove(ref); }
}
