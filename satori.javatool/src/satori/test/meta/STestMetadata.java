package satori.test.meta;

import java.util.ArrayList;
import java.util.List;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;

public class STestMetadata {
	private List<SInputMetadata> inputs = new ArrayList<SInputMetadata>();
	
	public Iterable<SInputMetadata> getInputs() { return inputs; }
	public void addInput(SInputMetadata im) { inputs.add(im); }
	
	public SAttributeReader getDefaultAttrs() {
		SAttributeMap attrs = SAttributeMap.createEmpty();
		for (SInputMetadata im : inputs) attrs.setAttr(im.getName(), im.getDefaultValue());
		return attrs;
	}
}
