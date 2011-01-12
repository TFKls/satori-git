package satori.test;

import satori.attribute.SFileAttribute;
import satori.common.SFile;

public class SFileInputMetadata extends InputMetadata {
	private final SFile def_value;
	
	public SFileInputMetadata(String name, String description, boolean required, SFile def_value) {
		super(name, description, required);
		this.def_value = def_value;
	}
	
	@Override public SFileAttribute getDefaultAttr() {
		return def_value != null ? new SFileAttribute(def_value) : null;
	}
	
	@Override public Input createInput(STestImpl test) { return new SFileInput(this, test); }
	
	@Override public SItemView createInputView(Input input) { return new SFileInputView(this, (SFileInput)input); }
}
