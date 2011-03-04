package satori.test.impl;

import java.util.ArrayList;
import java.util.List;

import satori.blob.SBlob;
import satori.common.SInput;
import satori.common.SListener0;
import satori.common.SView;

public class SSolution implements SInput<SBlob> {
	private SBlob blob;
	private final List<SListener0> modified_listeners = new ArrayList<SListener0>();
	private final List<SView> views = new ArrayList<SView>();
	
	@Override public SBlob get() { return blob; }
	@Override public String getDescription() { return "Solution file"; }
	@Override public boolean isValid() { return blob != null; }
	@Override public void set(SBlob blob) {
		if (blob == null && this.blob == null) return;
		if (blob != null && blob.equals(this.blob)) return;
		this.blob = blob;
		callModifiedListeners();
		updateViews();
	}
	
	public void addModifiedListener(SListener0 listener) { modified_listeners.add(listener); }
	public void removeModifiedListener(SListener0 listener) { modified_listeners.remove(listener); }
	private void callModifiedListeners() { for (SListener0 listener : modified_listeners) listener.call(); }
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { for (SView view : views) view.update(); }
}
