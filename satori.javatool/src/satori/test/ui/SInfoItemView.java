package satori.test.ui;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JTextField;

import satori.common.ui.SBlobInputView;
import satori.common.ui.SInputView;
import satori.common.ui.SPaneView;
import satori.test.impl.SJudgeInput;
import satori.test.impl.STestImpl;

public class SInfoItemView implements SPaneView {
	private final STestImpl test;
	
	private JComponent pane;
	private JTextField name_field;
	
	public SInfoItemView(STestImpl test) {
		this.test = test;
		test.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void updateName() { test.setName(name_field.getText()); }
	
	private void initialize() {
		pane = new Box(BoxLayout.Y_AXIS);
		name_field = new JTextField();
		SDimension.setItemSize(name_field);
		name_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateName(); }
		});
		name_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateName(); }
		});
		pane.add(name_field);
		SInputView judge_view = new SBlobInputView(new SJudgeInput(test));
		judge_view.setDimension(SDimension.itemDim);
		judge_view.setDescription("Judge file");
		test.addView(judge_view);
		pane.add(judge_view.getPane());
		update();
	}
	
	@Override public void update() {
		name_field.setText(test.getName());
	}
}
