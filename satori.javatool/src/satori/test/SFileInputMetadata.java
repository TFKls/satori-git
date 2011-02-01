package satori.test;

import satori.attribute.SFileAttribute;
import satori.common.SFile;
import satori.common.ui.SFileInputView;
import satori.common.ui.SPaneView;

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
	
	@Override public SPaneView createInputView(Input input) { 
		SFileInputView view = new SFileInputView((SFileInput)input);
		((SFileInput)input).addView(view);
		return view;
	}
}
