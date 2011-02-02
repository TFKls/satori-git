package satori.test.meta;

import satori.attribute.SStringAttribute;
import satori.common.ui.SPaneView;
import satori.common.ui.SStringInputView;
import satori.test.impl.Input;
import satori.test.impl.SStringInput;
import satori.test.impl.STestImpl;

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
	
	@Override public SPaneView createInputView(Input input) {
		SStringInputView view = new SStringInputView((SStringInput)input);
		((SStringInput)input).addView(view);
		return view;
	}
}
