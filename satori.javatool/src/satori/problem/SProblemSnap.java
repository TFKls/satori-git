package satori.problem;

import satori.common.SAssert;
import satori.common.SException;
import satori.common.SReference;
import satori.common.SReferenceList;
import satori.common.SView;
import satori.common.SViewList;

public class SProblemSnap implements SProblemReader {
	private long id;
	private String name;
	private String desc;
	
	private STestList test_list = null;
	private STestSuiteList suite_list = null;
	
	private final SViewList views = new SViewList();
	private final SReferenceList refs = new SReferenceList();
	
	@Override public boolean hasId() { return true; }
	@Override public long getId() { return id; }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	
	public STestList getTestList() { return test_list; }
	public STestSuiteList getTestSuiteList() { return suite_list; }
	
	private SProblemSnap() {}
	
	public static SProblemSnap create(SProblemReader source) {
		SProblemSnap self = new SProblemSnap();
		self.id = source.getId();
		self.name = source.getName();
		self.desc = source.getDescription();
		return self;
	}
	
	public void set(SProblemReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Problem ids don't match");
		name = source.getName();
		desc = source.getDescription();
		notifyModified();
	}
	
	private void notifyModified() {
		updateViews();
		refs.notifyModified();
	}
	public void notifyDeleted() {
		if (test_list != null) test_list.delete();
		test_list = null;
		if (suite_list != null) suite_list.delete();
		suite_list = null;
		refs.notifyDeleted();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void addReference(SReference ref) throws SException {
		if (test_list == null) test_list = STestList.createRemote(id);
		if (suite_list == null) suite_list = STestSuiteList.createRemote(id, test_list);
		refs.add(ref);
	}
	public void removeReference(SReference ref) {
		refs.remove(ref);
		if (refs.isEmpty()) {
			test_list = null;
			suite_list = null;
		}
	}
}
