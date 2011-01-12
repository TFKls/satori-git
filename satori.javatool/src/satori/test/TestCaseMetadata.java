package satori.test;

import java.util.ArrayList;
import java.util.List;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;

public class TestCaseMetadata extends Metadata {
	private List<InputMetadata> inputs = new ArrayList<InputMetadata>();
	
	public void addInput(InputMetadata im) { inputs.add(im); }
	
	public void createTestCase(STestImpl test) {
		for (InputMetadata im : inputs) test.addInput(im.createInput(test));
	}
	
	public void createTestPane(STestPane view) {
		for (InputMetadata im : inputs) view.addRow(im.createInputRowView());
	}
	
	public SAttributeReader getDefaultAttrs() {
		SAttributeMap attrs = SAttributeMap.createEmpty();
		for (InputMetadata im : inputs) attrs.setAttr(im.getName(), im.getDefaultAttr());
		return attrs;
	}
}
