package satori.problem.ui;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;

import satori.common.SView;
import satori.common.ui.STabPane;
import satori.common.ui.STabs;
import satori.main.SFrame;
import satori.problem.SParentProblem;
import satori.problem.impl.STestSuiteImpl;
import satori.task.STaskException;
import satori.test.impl.STestSuiteBase;
import satori.test.ui.STestPane;

public class STestSuitePane implements STabPane, SView {
	private final STabs parent;
	private final SParentProblem problem;
	private STestSuiteImpl suite = null;
	
	private STestSuiteInfoPane info_pane;
	private STestPane test_pane;
	private SParametersPane params_pane;
	private SView tab_view;
	
	private JComponent main_pane;
	private JLabel status_label;
	private JComponent button_pane;
	private JButton create_button, save_button, reload_button, delete_button, close_button;
	private JButton props_button, tests_button, params_button;
	private JScrollPane scroll_pane;
	
	@Override public JComponent getPane() { return main_pane; }
	public STestPane getTestPane() { return test_pane; }
	
	private STestSuitePane(STabs parent, SParentProblem problem) {
		this.parent = parent;
		this.problem = problem;
	}
	
	private class TabModel implements STabs.TabModel {
		@Override public String getTitle() {
			if (suite == null) return "(Tests)";
			else return suite.getName().isEmpty() ? "(Test suite)" : suite.getName();
		}
	}
	private void openTestsAux(STestSuiteBase base) {
		test_pane = new STestPane(problem, base);
		initialize();
		tab_view = parent.openPane(new TabModel(), this);
		test_pane.addParentView(tab_view);
	}
	private void openTestSuiteAux(STestSuiteImpl suite) {
		this.suite = suite;
		info_pane = new STestSuiteInfoPane(suite);
		test_pane = new STestPane(problem, suite.getBase());
		params_pane = new SParametersPane(suite);
		initialize();
		suite.addView(this);
		tab_view = parent.openPane(new TabModel(), this);
		suite.addView(tab_view);
		test_pane.addParentView(tab_view);
	}
	public static void openTests(STabs parent, SParentProblem problem, STestSuiteBase base) {
		new STestSuitePane(parent, problem).openTestsAux(base);
	}
	public static void openTestSuite(STabs parent, SParentProblem problem, STestSuiteImpl suite) {
		new STestSuitePane(parent, problem).openTestSuiteAux(suite);
	}
	@Override public boolean hasUnsavedData() {
		return suite != null && suite.isModified() || test_pane.getBase().hasModifiedTests();
	}
	@Override public void close() {
		test_pane.getBase().closeTests();
		if (suite != null) suite.close();
	}
	
	private void saveRequest() {
		if (!suite.isProblemRemote()) { SFrame.showErrorDialog("Cannot save: the problem does not exist remotely"); return; }
		if (!suite.hasNonremoteTests()) { SFrame.showErrorDialog("Cannot save: some tests do not exist remotely"); return; }
		try { if (suite.isRemote()) suite.save(); else suite.create(); }
		catch(STaskException ex) {}
	}
	private void reloadRequest() {
		if (!suite.isRemote()) return;
		try { suite.reload(); }
		catch(STaskException ex) { return; }
	}
	private void deleteRequest() {
		if (!suite.isRemote() || !SFrame.showWarningDialog("The test suite will be deleted.")) return;
		try { suite.delete(); }
		catch(STaskException ex) {}
	}
	private void closeRequest() {
		if (hasUnsavedData() && !SFrame.showWarningDialog("This tab contains unsaved data.")) return;
		close();
		parent.closePane(this);
	}
	private void createTestSuiteRequest() {
		if (suite != null) return;
		suite = STestSuiteImpl.createNew(problem, test_pane.getBase());
		suite.addView(this);
		suite.addView(tab_view);
		info_pane = new STestSuiteInfoPane(suite);
		params_pane = new SParametersPane(suite);
		button_pane.removeAll();
		initializeAux();
		button_pane.revalidate(); button_pane.repaint();
		update();
		tab_view.update();
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
		if (suite != null) {
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
		main_pane = new JPanel(new BorderLayout());
		Box upper_pane = new Box(BoxLayout.Y_AXIS);
		status_label = new JLabel();
		status_label.setAlignmentX(0.0f);
		upper_pane.add(status_label);
		button_pane = new Box(BoxLayout.X_AXIS);
		button_pane.setAlignmentX(0.0f);
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
		if (suite == null) {
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
