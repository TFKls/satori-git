package satori.common.ui;

import java.awt.Dimension;
import java.awt.Font;

import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.SOutput;

public class SStringOutputView implements SInputView {
	private final SOutput<String> data;
	
	private String desc;
	private JLabel label;
	private Font set_font, unset_font;
	
	public SStringOutputView(SOutput<String> data) {
		this.data = data;
		initialize();
	}
	
	@Override public JComponent getPane() { return label; }
	
	private void initialize() {
		label = new JLabel();
		set_font = label.getFont().deriveFont(Font.PLAIN);
		unset_font = label.getFont().deriveFont(Font.ITALIC);
		update();
	}
	
	@Override public void setDimension(Dimension dim) {
		label.setPreferredSize(dim);
		label.setMinimumSize(dim);
		label.setMaximumSize(dim);
		
	}
	@Override public void setDescription(String desc) {
		this.desc = desc;
		update();
		label.setToolTipText(desc);
	}
	
	@Override public void update() {
		label.setFont(data.get() != null ? set_font : unset_font);
		label.setText(data.get() != null ? data.get() : desc);
	}
}
