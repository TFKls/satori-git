package satori.common.ui;

import java.awt.Font;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.SwingConstants;

import satori.common.SData;

public class SStringOutputView implements SPaneView {
	private final SData<String> data;
	
	private JButton label;
	private Font set_font, unset_font;
	
	public SStringOutputView(SData<String> data) {
		this.data = data;
		initialize();
	}
	
	@Override public JComponent getPane() { return label; }
	
	private void initialize() {
		label = new JButton();
		label.setBorder(BorderFactory.createEmptyBorder(0, 1, 0, 1));
		label.setBorderPainted(false);
		label.setContentAreaFilled(false);
		label.setOpaque(false);
		label.setFocusable(false);
		label.setHorizontalAlignment(SwingConstants.LEADING);
		label.setToolTipText(data.getDescription());
		set_font = label.getFont().deriveFont(Font.PLAIN);
		unset_font = label.getFont().deriveFont(Font.ITALIC);
		update();
	}
	
	@Override public void update() {
		label.setFont(data.getText() != null ? set_font : unset_font);
		label.setText(data.getText() != null ? data.getText() : data.getDescription() != null ? data.getDescription() : "Not set");
	}
}
