package satori.test.ui;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;

import satori.common.ui.SBlobInputView;
import satori.common.ui.SInputView;
import satori.common.ui.SPane;
import satori.common.ui.SStringInputView;
import satori.test.impl.SBlobInput;
import satori.test.impl.SStringInput;
import satori.test.impl.STestImpl;
import satori.test.meta.SInputMetadata;
import satori.test.meta.STestMetadata;

public class SDataItemView implements SPane {
	private final STestMetadata meta;
	private final STestImpl test;
	
	private JComponent pane;
	
	public SDataItemView(STestMetadata meta, STestImpl test) {
		this.meta = meta;
		this.test = test;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new Box(BoxLayout.Y_AXIS);
		for (SInputMetadata im : meta.getInputs()) {
			SInputView view;
			if (im.isBlob()) view = new SBlobInputView(new SBlobInput(im, test));
			else view = new SStringInputView(new SStringInput(im, test));
			view.setDimension(SDimension.itemDim);
			view.setDescription(im.getDescription());
			test.addView(view);
			pane.add(view.getPane());
		}
		pane.add(Box.createVerticalGlue());
	}
}
