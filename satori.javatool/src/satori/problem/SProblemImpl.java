package satori.problem;

import satori.common.SAssert;
import satori.common.SDataStatus;
import satori.common.SException;
import satori.common.SId;
import satori.common.SReference;
import satori.common.SView;
import satori.common.SViewList;
import satori.server.SProblemData;

public class SProblemImpl implements SProblemReader, SParentProblem {
	private final SProblemList problem_list;
	
	private SProblemSnap snap = null;
	private SId id;
	private String name;
	private String desc;
	private STestList test_list;
	private STestSuiteList suite_list;
	
	private final SDataStatus status = new SDataStatus();
	private final SViewList views = new SViewList();
	private final SReference reference = new SReference() {
		@Override public void notifyModified() { snapModified(); }
		@Override public void notifyDeleted() { snapDeleted(); }
	};
	
	@Override public boolean hasId() { return id.isSet(); }
	@Override public long getId() { return id.get(); }
	@Override public String getName() { return name; }
	@Override public String getDescription() { return desc; }
	public boolean isRemote() { return hasId(); }
	public boolean isModified() { return status.isModified(); }
	public boolean isOutdated() { return status.isOutdated(); }
	
	@Override public STestList getTestList() { return test_list; }
	@Override public STestSuiteList getTestSuiteList() { return suite_list; }
	
	private SProblemImpl(SProblemList problem_list) {
		this.problem_list = problem_list;
	}
	
	public static SProblemImpl create(SProblemList problem_list, SProblemSnap snap) throws SException {
		SProblemImpl self = new SProblemImpl(problem_list);
		self.snap = snap;
		self.snap.addReference(self.reference);
		self.id = new SId(snap.getId());
		self.name = snap.getName();
		self.desc = snap.getDescription();
		self.test_list = self.snap.getTestList();
		self.suite_list = self.snap.getTestSuiteList();
		return self;
	}
	public static SProblemImpl createNew(SProblemList problem_list) {
		SProblemImpl self = new SProblemImpl(problem_list);
		self.id = new SId();
		self.name = "";
		self.desc = "";
		//TODO: correct the following
		self.test_list = STestList.createNew(-1);
		self.suite_list = STestSuiteList.createNew(-1, self.test_list);
		return self;
	}
	
	private boolean check(SProblemReader source) {
		SAssert.assertEquals(source.getId(), getId(), "Problem ids don't match");
		if (!source.getName().equals(name)) return true;
		if (!source.getDescription().equals(desc)) return true;
		return false;
	}
	
	public void set(SProblemReader source) {
		if (!check(source)) return;
		name = source.getName();
		desc = source.getDescription();
		notifyModified();
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
	
	private void snapModified() {
		if (!check(snap)) return;
		notifyOutdated();
	}
	private void snapDeleted() {
		snap = null;
		id.clear();
		notifyOutdated();
		test_list.delete(); //TODO: ?
		suite_list.delete(); //TODO: ?
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
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
	
	public void reload() throws SException {
		SAssert.assertTrue(isRemote(), "Problem not remote");
		set(SProblemData.load(getId()));
		notifyUpToDate();
		snap.set(this);
		test_list.reload();
		suite_list.reload();
	}
	public void create() throws SException {
		SAssert.assertFalse(isRemote(), "Problem already created");
		id.set(SProblemData.create(this));
		test_list.setProblemId(getId());
		suite_list.setProblemId(getId());
		notifyUpToDate();
		snap = SProblemSnap.create(this);
		snap.setTestList(test_list);
		snap.setTestSuiteList(suite_list);
		snap.addReference(reference);
		problem_list.addProblem(snap);
	}
	public void save() throws SException {
		SAssert.assertTrue(isRemote(), "Problem not remote");
		SProblemData.save(this);
		notifyUpToDate();
		snap.set(this);
	}
	public void delete() throws SException {
		SAssert.assertTrue(isRemote(), "Problem not remote");
		SProblemData.delete(getId());
		id.clear();
		notifyOutdated();
		snap.removeReference(reference);
		snap.notifyDeleted();
		problem_list.removeProblem(snap);
		snap = null;
		test_list.delete(); //TODO: ?
		suite_list.delete(); //TODO: ?
	}
	public void close() {
		if (snap == null) return;
		snap.removeReference(reference);
		snap = null;
	}
}
