package satori.test.ui;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;

import satori.common.SListener0;
import satori.common.ui.SBlobInputView;
import satori.common.ui.SInputView;
import satori.common.ui.SPane;
import satori.common.ui.SStringInputView;
import satori.test.impl.SBlobInput;
import satori.test.impl.SStringInput;
import satori.test.impl.STestImpl;
import satori.test.meta.SInputMetadata;

public class SDataItemView implements SPane {
	private final STestImpl test;
	
	private JComponent pane;
	
	public SDataItemView(STestImpl test) {
		this.test = test;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void fillPane() {
		for (SInputMetadata im : test.getMetadata().getInputs()) {
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
	private void initialize() {
		pane = new Box(BoxLayout.Y_AXIS);
		fillPane();
		test.addMetadataModifiedListener(new SListener0() {
			@Override public void call() {
				pane.removeAll();
				fillPane();
				pane.revalidate(); pane.repaint();
			}
		});
	}
}
