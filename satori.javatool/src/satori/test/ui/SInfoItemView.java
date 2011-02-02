package satori.test.ui;

import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;

import javax.swing.JComponent;
import javax.swing.JTextField;

import satori.common.ui.SPaneView;
import satori.test.impl.STestImpl;

public class SInfoItemView implements SPaneView {
	private STestImpl test;
	
	private JTextField name_field;
	
	private SInfoItemView(STestImpl test) {
		this.test = test;
		test.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return name_field; }
	
	private void updateName() { test.setName(name_field.getText()); }
	
	private void initialize() {
		name_field = new JTextField();
		name_field.setPreferredSize(new Dimension(120, 20));
		name_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateName(); }
		});
		name_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateName(); }
		});
		update();
	}
	
	@Override public void update() {
		name_field.setText(test.getName());
	}
	
	public static class Factory implements SItemViewFactory {
		@Override public SPaneView createView(STestImpl test) { return new SInfoItemView(test); }
	}
}
