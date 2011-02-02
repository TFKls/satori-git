package satori.test.meta;

import satori.attribute.SAttribute;
import satori.common.ui.SPaneView;
import satori.test.impl.Input;
import satori.test.impl.STestImpl;
import satori.test.ui.InputRowView;

public abstract class InputMetadata extends VarMetadata {
	private final boolean required;
	
	public boolean getRequired() { return required; }
	public abstract SAttribute getDefaultAttr();
	
	public InputMetadata(String name, String description, boolean required) {
		super(name, description);
		this.required = required;
	}
	
	public abstract Input createInput(STestImpl test);
	
	public abstract SPaneView createInputView(Input input);
	public InputRowView createInputRowView() { return new InputRowView(this); }
}
