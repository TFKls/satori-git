package satori.problem.ui;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;

import satori.common.SException;
import satori.common.SView;
import satori.common.ui.STabPane;
import satori.common.ui.STabs;
import satori.main.SFrame;
import satori.problem.impl.STestSuiteImpl;
import satori.test.impl.STestFactory;
import satori.test.ui.STestPane;

public class STestSuitePane implements STabPane, SView {
	private final STestSuiteImpl suite;
	private final STabs parent;
	private final STestFactory factory;
	
	private boolean mode;
	private STestSuiteInfoPane info_pane;
	private STestPane test_pane;
	private SParametersPane params_pane;
	private SView tab_view;
	
	private JPanel main_pane;
	private JLabel status_label;
	private JPanel button_pane;
	private JButton create_button, save_button, reload_button, delete_button, close_button;
	private JButton props_button, tests_button, params_button;
	private JScrollPane scroll_pane;
	
	public STestSuitePane(STestSuiteImpl suite, STabs parent, STestFactory factory, boolean mode) {
		this.suite = suite;
		this.parent = parent;
		this.factory = factory;
		this.mode = mode;
		initialize();
	}
	
	@Override public JComponent getPane() { return main_pane; }
	public STestPane getTestPane() { return test_pane; }
	
	private static class TabModel implements STabs.TabModel {
		private final STestSuiteImpl suite;
		public TabModel(STestSuiteImpl suite) { this.suite = suite; }
		@Override public String getTitle() {
			return suite.getName().isEmpty() ? "(Tests)" : suite.getName();
		}
	}
	public void open() {
		suite.addView(this);
		tab_view = parent.openPane(new TabModel(suite), this);
		suite.addView(tab_view);
		test_pane.addParentView(tab_view);
	}
	@Override public boolean hasUnsavedData() {
		return mode && suite.isModified() || test_pane.hasUnsavedData();
	}
	@Override public void close() {
		test_pane.removeAll();
		suite.close();
	}
	
	private void saveRequest() {
		if (!suite.isProblemRemote()) { SFrame.showErrorDialog("Cannot save: the problem does not exist remotely"); return; }
		if (!suite.hasNonremoteTests()) { SFrame.showErrorDialog("Cannot save: some tests do not exist remotely"); return; }
		try { if (suite.isRemote()) suite.save(); else suite.create(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void reloadRequest() {
		if (!suite.isRemote()) return;
		try { suite.reload(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
		test_pane.removeAll();
		test_pane.add(suite.getTests());
	}
	private void deleteRequest() {
		if (!suite.isRemote() || !SFrame.showWarningDialog("The test suite will be deleted.")) return;
		try { suite.delete(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void closeRequest() {
		if (hasUnsavedData() && !SFrame.showWarningDialog("This tab contains unsaved data.")) return;
		close();
		parent.closePane(this);
	}
	private void createTestSuiteRequest() {
		if (mode) return;
		mode = true;
		button_pane.removeAll();
		initializeAux();
		button_pane.revalidate(); button_pane.repaint();
		update();
	}
	private void showPropertiesRequest() {
		scroll_pane.setBorder(BorderFactory.createTitledBorder("Test suite properties"));
		scroll_pane.setViewportView(info_pane.getPane());
	}
	private void showTestsRequest() {
		scroll_pane.setBorder(BorderFactory.createTitledBorder("Tests"));
		scroll_pane.setViewportView(test_pane.getPane());
	}
	private void showParametersRequest() {
		scroll_pane.setBorder(BorderFactory.createTitledBorder("Parameters"));
		scroll_pane.setViewportView(params_pane.getPane());
	}
	
	private void initializeAux() {
		if (mode) {
			button_pane.add(props_button);
			button_pane.add(tests_button);
			button_pane.add(params_button);
			button_pane.add(Box.createHorizontalStrut(5));
			button_pane.add(save_button);
			button_pane.add(reload_button);
			button_pane.add(delete_button);
			button_pane.add(Box.createHorizontalStrut(5));
			button_pane.add(close_button);
			showPropertiesRequest();
		} else {
			button_pane.add(create_button);
			button_pane.add(Box.createHorizontalStrut(5));
			button_pane.add(close_button);
			showTestsRequest();
		}
	}
	private void initialize() {
		info_pane = new STestSuiteInfoPane(suite);
		test_pane = new STestPane(suite, factory);
		params_pane = new SParametersPane(suite);
		
		main_pane = new JPanel(new BorderLayout());
		JPanel upper_pane = new JPanel(new BorderLayout());
		status_label = new JLabel();
		upper_pane.add(status_label, BorderLayout.NORTH);
		button_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		create_button = new JButton("Create test suite");
		create_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { createTestSuiteRequest(); }
		});
		save_button = new JButton("Save");
		save_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { saveRequest(); }
		});
		reload_button = new JButton("Reload");
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		delete_button = new JButton("Delete");
		delete_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { deleteRequest(); }
		});
		close_button = new JButton("Close");
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeRequest(); }
		});
		props_button = new JButton("Properties");
		props_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { showPropertiesRequest(); }
		});
		tests_button = new JButton("Tests");
		tests_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { showTestsRequest(); }
		});
		params_button = new JButton("Parameters");
		params_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { showParametersRequest(); }
		});
		upper_pane.add(button_pane, BorderLayout.CENTER);
		main_pane.add(upper_pane, BorderLayout.NORTH);
		scroll_pane = new JScrollPane();
		main_pane.add(scroll_pane, BorderLayout.CENTER);
		initializeAux();
		update();
	}
	
	@Override public void update() {
		if (!mode) {
			status_label.setText("Status: no test suite");
			return;
		}
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
		info_pane.update(); //TODO: necessary?
	}
}
