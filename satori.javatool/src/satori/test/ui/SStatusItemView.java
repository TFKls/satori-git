package satori.test.ui;

import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.ui.SPaneView;
import satori.test.impl.STestImpl;

public class SStatusItemView implements SPaneView {
	private final STestImpl test;
	
	private JLabel label;
	
	public SStatusItemView(STestImpl test) {
		this.test = test;
		test.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return label; }
	
	private void initialize() {
		label = new JLabel();
		SDimension.setItemSize(label);
		update();
	}
	
	@Override public void update() {
		String status_text = "";
		if (test.isRemote()) {
			if (test.isOutdated()) status_text = "outdated";
		} else {
			if (test.isOutdated()) status_text = "deleted";
			else status_text = "new";
		}
		if (test.isModified()) {
			if (!status_text.isEmpty()) status_text += ", ";
			status_text += "modified";
		}
		if (status_text.isEmpty()) status_text = "saved";
		label.setText(status_text);
	}
}
