package satori.test;

import satori.common.SData;
import satori.common.SFile;
import satori.common.SListener0;
import satori.common.SListener0List;
import satori.common.SView;
import satori.common.SViewList;

public class SSolution implements SData<SFile> {
	private SFile file;
	private final SListener0List modified_listeners = new SListener0List();
	private final SViewList views = new SViewList();
	
	@Override public SFile get() { return file; }
	@Override public void set(SFile file) {
		if (file == this.file) return;
		this.file = file;
		callModifiedListeners();
		updateViews();
	}
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() { return file != null; }
	
	public void addModifiedListener(SListener0 listener) { modified_listeners.add(listener); }
	public void removeModifiedListener(SListener0 listener) { modified_listeners.remove(listener); }
	private void callModifiedListeners() { modified_listeners.call(); }
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
}
