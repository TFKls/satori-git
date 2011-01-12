package satori.test;

import java.io.File;

import satori.attribute.SFileAttribute;
import satori.common.SFile;
import satori.common.SView;
import satori.common.SViewList;

public class SFileInput extends Input {
	public static enum Status { VALID, INVALID, DISABLED };
	
	private final SFileInputMetadata meta;
	private final STestImpl test;
	
	private SFile data;
	
	private final SViewList views = new SViewList();
	
	public SFileInput(SFileInputMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
	}
	
	public SFileInputMetadata getMetadata() { return meta; }
	public SFile getData() { return data; }
	
	public String getName() { return data == null ? null : data.getName(); }
	public File getFile() { return data == null ? null : data.getFile(); }
	public boolean isRemote() { return data == null ? false : data.isRemote(); }
	public boolean isDataSet() { return data != null; }
	
	public Status getStatus() {
		if (meta.getRequired() && data == null) return Status.INVALID;
		else return Status.VALID;
	}
	
	public void update() {
		data = test.getData().getBlob(meta.getName());
		updateViews();
	}
	
	public void setData(SFile data) {
		if (data == this.data) return; //TODO: compare files
		this.data = data;
		test.setAttr(meta.getName(), new SFileAttribute(data));
		updateViews();
	}
	public void setLocal(File file) {
		data = SFile.createLocal(file);
		test.setAttr(meta.getName(), new SFileAttribute(data));
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
