package satori.test.ui;

import java.awt.Font;

import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.ui.SPaneView;
import satori.test.impl.STestResult;

public class SResultStatusItemView implements SPaneView {
	private final STestResult result;
	
	private JLabel label;
	private Font normal_font, message_font;
	
	public SResultStatusItemView(STestResult result) {
		this.result = result;
		result.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return label; }
	
	private void initialize() {
		label = new JLabel();
		SDimension.setItemSize(label);
		normal_font = label.getFont().deriveFont(Font.PLAIN);
		message_font = label.getFont().deriveFont(Font.BOLD);
		update();
	}
	
	@Override public void update() {
		switch (result.getStatus()) {
		case NOT_TESTED:
			label.setFont(normal_font);
			label.setText("Not tested");
			break;
		case PENDING:
			label.setFont(normal_font);
			label.setText("Pending");
			break;
		case FINISHED:
			label.setFont(message_font);
			label.setText(result.getMessage());
			break;
		}
	}
}
