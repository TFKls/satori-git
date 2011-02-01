package satori.test;

import satori.attribute.SFileAttribute;
import satori.common.SFile;
import satori.common.SData;
import satori.common.SView;
import satori.common.SViewList;

public class SFileInput extends Input implements SData<SFile> {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final SFileInputMetadata meta;
	private final STestImpl test;
	
	private SFile data;
	
	private final SViewList views = new SViewList();
	
	public SFileInput(SFileInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	@Override public SFileInputMetadata getMetadata() { return meta; }
	
	@Override public SFile get() { return data; }
	@Override public void set(SFile data) {
		if (data == this.data) return; //TODO: compare files
		this.data = data;
		test.setAttr(meta.getName(), new SFileAttribute(data));
		updateViews();
	}
	
	public Status getStatus() {
		if (meta.getRequired() && data == null) return Status.INVALID;
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
