package satori.test.meta;

import java.util.ArrayList;
import java.util.List;

import satori.attribute.SAttributeMap;
import satori.attribute.SAttributeReader;
import satori.test.impl.SBlobInput;
import satori.test.impl.SStringInput;
import satori.test.impl.STestImpl;
import satori.test.ui.InputRowView;
import satori.test.ui.STestInputPane;

public class TestCaseMetadata {
	private List<InputMetadata> inputs = new ArrayList<InputMetadata>();
	
	public void addInput(InputMetadata im) { inputs.add(im); }
	
	public void createTestCase(STestImpl test) {
		for (InputMetadata im : inputs) {
			if (im.isBlob()) test.addInput(new SBlobInput(im, test));
			else test.addInput(new SStringInput(im, test));
		}
	}
	
	public void createTestPane(STestInputPane view) {
		for (InputMetadata im : inputs) view.addRow(new InputRowView(im));
	}
	
	public SAttributeReader getDefaultAttrs() {
		SAttributeMap attrs = SAttributeMap.createEmpty();
		for (InputMetadata im : inputs) attrs.setAttr(im.getName(), im.getDefaultValue());
		return attrs;
	}
}
