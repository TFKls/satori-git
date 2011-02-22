package satori.test.impl;

import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SListener0;
import satori.common.SListener0List;
import satori.common.SView;
import satori.common.SViewList;

public class SSolution implements SData<SBlob> {
	private SBlob blob;
	private final SListener0List modified_listeners = new SListener0List();
	private final SViewList views = new SViewList();
	
	@Override public SBlob get() { return blob; }
	@Override public boolean isEnabled() { return true; }
	@Override public boolean isValid() { return blob != null; }
	@Override public void update() {}
	@Override public void set(SBlob blob) {
		if (blob == null && this.blob == null) return;
		if (blob != null && blob.equals(this.blob)) return;
		this.blob = blob;
		callModifiedListeners();
		updateViews();
	}
	
	public void addModifiedListener(SListener0 listener) { modified_listeners.add(listener); }
	public void removeModifiedListener(SListener0 listener) { modified_listeners.remove(listener); }
	private void callModifiedListeners() { modified_listeners.call(); }
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
}
