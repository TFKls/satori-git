package satori.test.ui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.ui.SPaneView;
import satori.test.impl.STestResult;

public class SResultStatusItemView implements SPaneView {
	private final STestResult result;
	
	private JPanel pane;
	private JLabel label;
	private Font normal_font, message_font;
	private Color default_color;
	
	public SResultStatusItemView(STestResult result) {
		this.result = result;
		result.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label = new JLabel();
		label.setPreferredSize(new Dimension(120, 20));
		label.setHorizontalAlignment(JLabel.CENTER);
		pane.add(label);
		normal_font = label.getFont().deriveFont(Font.PLAIN);
		message_font = label.getFont().deriveFont(Font.BOLD);
		default_color = pane.getBackground();
		update();
	}
	
	@Override public void update() {
		switch (result.getStatus()) {
		case NOT_TESTED:
			pane.setBackground(default_color);
			label.setFont(normal_font);
			label.setText("Not tested");
			break;
		case PENDING:
			pane.setBackground(Color.YELLOW);
			label.setFont(normal_font);
			label.setText("Pending");
			break;
		case FINISHED:
			pane.setBackground("OK".equals(result.getMessage()) ? Color.GREEN : Color.RED);
			label.setFont(message_font);
			label.setText(result.getMessage());
			break;
		}
	}
}
