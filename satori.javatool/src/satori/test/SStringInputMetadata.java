package satori.test;

import satori.attribute.SStringAttribute;

public class SStringInputMetadata extends InputMetadata {
	public final String def_value;
	
	public SStringInputMetadata(String name, String description, boolean required, String def_value) {
		super(name, description, required);
		this.def_value = def_value;
	}
	
	@Override public SStringAttribute getDefaultAttr() {
		if (def_value == null || def_value.isEmpty()) return null;
		return new SStringAttribute(def_value);
	}
	
	@Override public Input createInput(STestImpl test) { return new SStringInput(this, test); }
	
	@Override public SItemView createInputView(Input input) { return new SStringInputView(this, (SStringInput)input); }
}
