package satori.test.impl;

import satori.attribute.SBlobAttribute;
import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SView;
import satori.common.SViewList;
import satori.test.meta.InputMetadata;

public class SBlobInput extends Input implements SData<SBlob> {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final InputMetadata meta;
	private final STestImpl test;
	
	private SBlob data;
	
	private final SViewList views = new SViewList();
	
	public SBlobInput(InputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public InputMetadata getMetadata() { return meta; }
	
	@Override public SBlob get() { return data; }
	@Override public void set(SBlob data) {
		if (data == this.data) return; //TODO: compare files
		this.data = data;
		test.setAttr(meta.getName(), data != null ? new SBlobAttribute(data) : null);
		updateViews();
	}
	
	public Status getStatus() {
		if (meta.isRequired() && data == null) return Status.INVALID;
		else return Status.VALID;
	}
	
	@Override public boolean isEnabled() { return getStatus() != Status.DISABLED; }
	@Override public boolean isValid() { return getStatus() == Status.VALID; }
	
	@Override public void update() {
		data = test.getData().getBlob(meta.getName());
		updateViews();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
}
