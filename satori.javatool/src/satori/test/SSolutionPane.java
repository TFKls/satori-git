package satori.test;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.List;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.SException;
import satori.common.SListener;
import satori.common.SListener0;
import satori.common.ui.SFileInputView;
import satori.main.SFrame;

public class SSolutionPane implements SRowView {
	private final SSolution solution;
	private final SListener<SSolutionPane> remove_listener;
	private final List<STestResult> results = new ArrayList<STestResult>();
	private final SListener0 run_all_listener = new SListener0() {
		@Override public void call() { runAll(); }
	};
	private final SListener0 refresh_all_listener = new SListener0() {
		@Override public void call() { refreshAll(); }
	};
	
	private JPanel pane;
	private JPanel solution_pane;
	private SFileInputView solution_input;
	private SResultButtonRowView button_row;
	private SResultStatusRowView status_row;
	
	public SSolutionPane(SSolution solution, SListener<SSolutionPane> remove_listener) {
		this.solution = solution;
		this.remove_listener = remove_listener;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void runAll() {
		try { for (STestResult result : results) result.run(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); }
	}
	private void refreshAll() {
		try { for (STestResult result : results) result.refresh(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); }
	}
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new BoxLayout(pane, BoxLayout.Y_AXIS));
		solution_pane = new JPanel();
		solution_pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		JLabel solution_label = new JLabel("Solution");
		solution_label.setPreferredSize(new Dimension(120, 20));
		solution_pane.add(solution_label);
		solution_input = new SFileInputView(solution);
		solution.addView(solution_input);
		solution_pane.add(solution_input.getPane());
		JButton remove_button = new JButton("X");
		remove_button.setMargin(new Insets(0, 0, 0, 0));
		remove_button.setPreferredSize(new Dimension(24, 20));
		remove_button.setToolTipText("Remove solution");
		remove_button.setFocusable(false);
		remove_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { remove_listener.call(SSolutionPane.this); }
		});
		solution_pane.add(remove_button);
		pane.add(solution_pane);
		button_row = new SResultButtonRowView(run_all_listener, refresh_all_listener);
		pane.add(button_row.getPane());
		status_row = new SResultStatusRowView();
		pane.add(status_row.getPane());
	}

	@Override public void addColumn(STestImpl test, int index) {
		STestResult result = new STestResult(solution, test);
		results.add(index, result);
		button_row.addColumn(result, index);
		status_row.addColumn(result, index);
	}
	@Override public void removeColumn(int index) {
		button_row.removeColumn(index);
		status_row.removeColumn(index);
		results.get(index).close();
		results.remove(index);
	}
}
