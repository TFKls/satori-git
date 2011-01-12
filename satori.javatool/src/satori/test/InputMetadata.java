package satori.test;

import satori.attribute.SAttribute;

public abstract class InputMetadata extends VarMetadata {
	private final boolean required;
	
	public boolean getRequired() { return required; }
	public abstract SAttribute getDefaultAttr();
	
	public InputMetadata(String name, String description, boolean required) {
		super(name, description);
		this.required = required;
	}
	
	public abstract Input createInput(STestImpl test);
	
	public abstract SItemView createInputView(Input input);
	public InputRowView createInputRowView() { return new InputRowView(this); }
}
