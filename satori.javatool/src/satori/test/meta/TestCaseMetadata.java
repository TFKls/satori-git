package satori.test.meta;

import java.util.ArrayList;
import java.util.List;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;

public class TestCaseMetadata {
	private List<InputMetadata> inputs = new ArrayList<InputMetadata>();
	
	public Iterable<InputMetadata> getInputs() { return inputs; }
	public void addInput(InputMetadata im) { inputs.add(im); }
	
	public SAttributeReader getDefaultAttrs() {
		SAttributeMap attrs = SAttributeMap.createEmpty();
		for (InputMetadata im : inputs) attrs.setAttr(im.getName(), im.getDefaultValue());
		return attrs;
	}
}
