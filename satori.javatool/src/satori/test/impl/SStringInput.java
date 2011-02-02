package satori.test.impl;

import satori.attribute.SStringAttribute;
import satori.common.SData;
import satori.common.SView;
import satori.common.SViewList;
import satori.test.meta.InputMetadata;

public class SStringInput extends Input implements SData<String> {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final InputMetadata meta;
	private final STestImpl test;
	
	private String data;
	
	private final SViewList views = new SViewList();
	
	public SStringInput(InputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public InputMetadata getMetadata() { return meta; }
	
	@Override public String get() { return data; }
	@Override public void set(String data) {
		if (data == null && this.data == null) return;
		if (data != null && data.equals(this.data)) return;
		this.data = data;
		test.setAttr(meta.getName(), data != null ? new SStringAttribute(data) : null);
		updateViews();
	}
	
	public Status getStatus() {
		if (meta.isRequired() && data == null) return Status.INVALID;
		else return Status.VALID;
	}
	
	@Override public boolean isEnabled() { return getStatus() != Status.DISABLED; }
	@Override public boolean isValid() { return getStatus() == Status.VALID; }
	
	@Override public void update() {
		data = test.getData().getString(meta.getName());
		updateViews();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
}
