package satori.test;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;
import satori.common.SAssert;
import satori.common.SException;
import satori.common.SListener;
import satori.common.SListenerList;
import satori.common.SReference;
import satori.common.SReferenceList;
import satori.common.SView;
import satori.common.SViewList;
import satori.thrift.STestData;

public class STestSnap implements STestReader {
	private long id;
	private long problem_id;
	private String name;
	private SAttributeMap attrs;
	
	private final SViewList views = new SViewList();
	private final SReferenceList refs = new SReferenceList();
	private final SListenerList<STestSnap> deleted = new SListenerList<STestSnap>();
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public long getProblemId() { return problem_id; }
	@Override public String getName() { return name; }
	@Override public SAttributeReader getData() { return attrs; }
	
	public boolean isComplete() { return attrs != null; }
	
	private STestSnap() {}
	
	public static STestSnap create(STestReader source) {
		STestSnap self = new STestSnap();
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.attrs = SAttributeMap.create(source.getData());
		return self;
	}
	public static STestSnap createBasic(STestBasicReader source) {
		STestSnap self = new STestSnap();
		self.id = source.getId();
		self.problem_id = source.getProblemId();
		self.name = source.getName();
		self.attrs = null;
		return self;
	}
	
	public void set(STestReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Test ids don't match");
		SAssert.assertEquals(source.getProblemId(), getProblemId(), "Problem ids don't match");
		name = source.getName();
		attrs = SAttributeMap.create(source.getData());
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
		updateViews();
		refs.notifyModified();
	}
	public void notifyDeleted() {
		deleted.call(this);
		refs.notifyDeleted();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void addDeletedListener(SListener<STestSnap> listener) { deleted.add(listener); }
	public void removeDeletedListener(SListener<STestSnap> listener) { deleted.remove(listener); }
	
	public void addReference(SReference ref) { refs.add(ref); }
	public void removeReference(SReference ref) { refs.remove(ref); }
}
