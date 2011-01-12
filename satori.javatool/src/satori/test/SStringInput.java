package satori.test;

import satori.attribute.SStringAttribute;
import satori.common.SView;
import satori.common.SViewList;

public class SStringInput extends Input {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final SStringInputMetadata meta;
	private final STestImpl test;
	
	private String data;
	
	private final SViewList views = new SViewList();
	
	public SStringInput(SStringInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	public SStringInputMetadata getMetadata() { return meta; }
	public String getData() { return data; }
	
	public String getValue() { return data; }
	public boolean isDataSet() { return data != null; }
	
	public Status getStatus() {
		if (meta.getRequired() && data == null) return Status.INVALID;
		else return Status.VALID;
	}
	
	public void update() {
		data = test.getData().getString(meta.getName());
		updateViews();
	}
	
	public void setValue(String data) {
		if (data.equals(this.data)) return;
		this.data = data;
		test.setAttr(meta.getName(), new SStringAttribute(data));
		updateViews();
	}
	public void clearData() {
		if (data == null) return;
		data = null;
		test.setAttr(meta.getName(), null);
		updateViews();
	}
	
	public void addView(SView view) { views.add(view); }
	public void removeView(SView view) { views.remove(view); }
	private void updateViews() { views.update(); }
}
