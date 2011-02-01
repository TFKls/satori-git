package satori.test;

import satori.attribute.SBlobAttribute;
import satori.blob.SBlob;
import satori.common.ui.SBlobInputView;
import satori.common.ui.SPaneView;

public class SBlobInputMetadata extends InputMetadata {
	private final SBlob def_value;
	
	public SBlobInputMetadata(String name, String description, boolean required, SBlob def_value) {
		super(name, description, required);
		this.def_value = def_value;
	}
	
	@Override public SBlobAttribute getDefaultAttr() {
		return def_value != null ? new SBlobAttribute(def_value) : null;
	}
	
	@Override public Input createInput(STestImpl test) { return new SBlobInput(this, test); }
	
	@Override public SPaneView createInputView(Input input) { 
		SBlobInputView view = new SBlobInputView((SBlobInput)input);
		((SBlobInput)input).addView(view);
		return view;
	}
}
