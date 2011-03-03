package satori.problem;

import java.util.ArrayList;
import java.util.List;

import satori.common.SAssert;
import satori.common.SException;
import satori.common.SReference;
import satori.common.SView;
import satori.thrift.SProblemData;

public class SProblemSnap implements SProblemReader {
	private long id;
	private String name;
	private String desc;
	
	private STestList test_list = null;
	private STestSuiteList suite_list = null;
	
	private final List<SView> views = new ArrayList<SView>();
	private final List<SReference> refs = new ArrayList<SReference>();
	
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
	public void reload() throws SException {
		set(SProblemData.load(id));
		if (test_list != null) test_list.reload();
		if (suite_list != null) suite_list.reload();
	}
	
	private void notifyModified() {
		for (SView view : views) view.update();
		for (SReference ref : refs) ref.notifyModified();
	}
	public void notifyDeleted() {
		if (test_list != null) test_list.delete();
		test_list = null;
		if (suite_list != null) suite_list.delete();
		suite_list = null;
		for (SReference ref : refs) ref.notifyDeleted();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	
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
