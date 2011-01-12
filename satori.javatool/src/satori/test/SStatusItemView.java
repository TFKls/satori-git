package satori.test;

import java.awt.Dimension;

import javax.swing.JComponent;
import javax.swing.JLabel;

public class SStatusItemView implements SItemView {
	private final STestImpl test;
	
	private JLabel label;
	
	private SStatusItemView(STestImpl test) {
		this.test = test;
		test.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return label; }
	
	private void initialize() {
		label = new JLabel();
		label.setPreferredSize(new Dimension(120, 20));
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
	
	public static class Factory implements SItemViewFactory {
		@Override public SItemView createView(STestImpl test) { return new SStatusItemView(test); }
	}
}
