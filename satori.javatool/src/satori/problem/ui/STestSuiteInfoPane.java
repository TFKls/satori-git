package satori.problem.ui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;

import satori.common.SView;
import satori.common.ui.SPane;
import satori.problem.impl.STestSuiteImpl;

public class STestSuiteInfoPane implements SPane, SView {
	private final STestSuiteImpl suite;
	
	private JPanel pane;
	private JTextField name_field;
	private JTextField desc_field;
	
	public STestSuiteInfoPane(STestSuiteImpl suite) {
		this.suite = suite;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void updateName() { suite.setName(name_field.getText()); }
	private void updateDescription() { suite.setDescription(desc_field.getText()); }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new GridBagLayout());
		GridBagConstraints c = new GridBagConstraints();
		c.gridx = 0; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 0.0; c.weighty = 0.0;
		pane.add(new JLabel("Name: "), c);
		pane.add(new JLabel("Description: "), c);
		c.gridx = 1; c.gridy = GridBagConstraints.RELATIVE; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1.0; c.weighty = 0.0;
		name_field = new JTextField();
		name_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateName(); }
		});
		name_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateName(); }
		});
		pane.add(name_field, c);
		desc_field = new JTextField();
		desc_field.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { updateDescription(); }
		});
		desc_field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { updateDescription(); }
		});
		pane.add(desc_field, c);
		update();
	}
	
	@Override public void update() {
		name_field.setText(suite.getName());
		desc_field.setText(suite.getDescription());
	}
}
