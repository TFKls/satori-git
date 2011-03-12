package satori.problem.ui;

import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JTextField;

import satori.common.SView;
import satori.common.ui.SPane;
import satori.problem.impl.SProblemImpl;

public class SProblemInfoPane implements SPane, SView {
	private final SProblemImpl problem;
	
	private JComponent pane;
	private JTextField name_field;
	private JTextField desc_field;
	
	public SProblemInfoPane(SProblemImpl problem) {
		this.problem = problem;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void updateName() { problem.setName(name_field.getText()); }
	private void updateDescription() { problem.setDescription(desc_field.getText()); }
	
	private static JComponent setLabelSizes(JComponent comp) {
		Dimension dim = new Dimension(100, 20);
		comp.setPreferredSize(dim);
		comp.setMinimumSize(dim);
		comp.setMaximumSize(dim);
		return comp;
	}
	private void initialize() {
		pane = new Box(BoxLayout.X_AXIS);
		Box pane1 = new Box(BoxLayout.Y_AXIS);
		Box pane2 = new Box(BoxLayout.Y_AXIS);
		pane1.add(setLabelSizes(new JLabel("Name")));
		pane1.add(setLabelSizes(new JLabel("Description")));
		name_field = new JTextField();
		name_field.setPreferredSize(new Dimension(480, 20));
		name_field.setMinimumSize(new Dimension(480, 20));
		name_field.setMaximumSize(new Dimension(480, 20));
		name_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateName(); }
		});
		name_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateName(); }
		});
		pane2.add(name_field);
		desc_field = new JTextField();
		desc_field.setPreferredSize(new Dimension(480, 20));
		desc_field.setMinimumSize(new Dimension(480, 20));
		desc_field.setMaximumSize(new Dimension(480, 20));
		desc_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateDescription(); }
		});
		desc_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateDescription(); }
		});
		pane2.add(desc_field);
		pane.add(pane1);
		pane.add(Box.createHorizontalStrut(5));
		pane.add(pane2);
		pane.add(Box.createHorizontalGlue());
		update();
	}
	
	@Override public void update() {
		name_field.setText(problem.getName());
		desc_field.setText(problem.getDescription());
	}
}
