package satori.problem.ui;

import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.SException;
import satori.common.SView;
import satori.common.ui.SPane;
import satori.common.ui.STabs;
import satori.main.SFrame;
import satori.problem.impl.STestSuiteImpl;
import satori.test.impl.STestFactory;
import satori.test.ui.STestPane;

public class STestSuitePane implements SPane, SView {
	private final STestSuiteImpl suite;
	private final STabs parent;
	private final STestFactory factory;
	
	private STestSuiteInfoPane info_pane;
	private STestPane test_pane;
	private SView tab_view;
	
	private JPanel main_pane;
	private JLabel status_label;
	private JPanel button_pane;
	private JButton save_button, reload_button, delete_button, close_button;
	
	public STestSuitePane(STestSuiteImpl suite, STabs parent, STestFactory factory) {
		this.suite = suite;
		this.parent = parent;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return main_pane; }
	public STestPane getTestPane() { return test_pane; }
	
	private static class TabModel implements STabs.TabModel {
		private final STestSuiteImpl suite;
		public TabModel(STestSuiteImpl suite) { this.suite = suite; }
		@Override public String getTitle() {
			String title = suite.getName().isEmpty() ? "(Tests)" : suite.getName();
			if (suite.isModified()) title += "*";
			return title;
		}
	}
	public void open() {
		suite.addView(this);
		tab_view = parent.openPane(new TabModel(suite), this);
		suite.addView(tab_view);
	}
	private void close() {
		suite.removeView(tab_view);
		parent.closePane(this);
		suite.removeView(this);
	}
	
	private boolean askUnsaved() { return SFrame.showWarningDialog("Unsaved changes to the test suite will be lost."); }
	
	private void saveRequest() {
		if (!suite.isSaveable()) { SFrame.showErrorDialog("Cannot save test suite with new tests"); return; }
		try { if (suite.isRemote()) suite.save(); else suite.create(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void reloadRequest() {
		if (!suite.isRemote() || suite.isModifiedRecursive() && !askUnsaved()) return;
		try { suite.reload(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void deleteRequest() {
		if (!suite.isRemote() || !SFrame.showWarningDialog("The test suite will be deleted.")) return;
		try { suite.delete(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void closeRequest() {
		if (suite.isModifiedRecursive() && !askUnsaved()) return;
		suite.close();
		close();
	}
	
	private void initialize() {
		info_pane = new STestSuiteInfoPane(suite);
		test_pane = new STestPane(suite, factory);
		
		main_pane = new JPanel(new GridBagLayout());
		GridBagConstraints c = new GridBagConstraints();
		c.gridx = 0; c.gridy = 0; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1.0; c.weighty = 0.0; c.gridwidth = 1;
		status_label = new JLabel();
		main_pane.add(status_label, c);
		c.gridx = 0; c.gridy = 1; c.fill = GridBagConstraints.HORIZONTAL; c.weightx = 1.0; c.weighty = 0.0; c.gridwidth = 1;
		button_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		save_button = new JButton("Save");
		save_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { saveRequest(); }
		});
		button_pane.add(save_button);
		reload_button = new JButton("Reload");
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		button_pane.add(reload_button);
		delete_button = new JButton("Delete");
		delete_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { deleteRequest(); }
		});
		button_pane.add(delete_button);
		close_button = new JButton("Close");
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeRequest(); }
		});
		button_pane.add(close_button);
		main_pane.add(button_pane, c);
		info_pane.getPane().setBorder(BorderFactory.createTitledBorder("Test suite properties"));
		c.gridx = 0; c.gridy = 2; c.fill = GridBagConstraints.BOTH; c.weightx = 1.0; c.weighty = 0.0; c.gridwidth = 1;
		main_pane.add(info_pane.getPane(), c);
		test_pane.getPane().setBorder(BorderFactory.createTitledBorder("Tests"));
		c.gridx = 0; c.gridy = 3; c.fill = GridBagConstraints.BOTH; c.weightx = 1.0; c.weighty = 1.0; c.gridwidth = 1;
		main_pane.add(test_pane.getPane(), c);
		update();
	}
	
	@Override public void update() {
		reload_button.setEnabled(suite.isRemote());
		delete_button.setEnabled(suite.isRemote());
		String status_text = "";
		if (suite.isRemote()) {
			if (suite.isOutdated()) status_text = "outdated";
		} else {
			if (suite.isOutdated()) status_text = "deleted";
			else status_text = "new";
		}
		if (suite.isModified()) {
			if (!status_text.isEmpty()) status_text += ", ";
			status_text += "modified";
		}
		if (status_text.isEmpty()) status_text = "saved";
		status_label.setText("Status: " + status_text);
		info_pane.update();
	}
}
