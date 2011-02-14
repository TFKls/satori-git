package satori.test.ui;

import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.List;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.SException;
import satori.common.SListener1;
import satori.common.SView;
import satori.common.ui.SBlobInputView;
import satori.common.ui.SPane;
import satori.main.SFrame;
import satori.test.impl.SSolution;
import satori.test.impl.STestImpl;
import satori.test.impl.STestResult;

public class SSolutionPane implements SRow {
	private final SSolution solution;
	private final SListener1<SSolutionPane> remove_listener;
	private final List<STestResult> results = new ArrayList<STestResult>();
	
	private JComponent pane;
	private SBlobInputView solution_input;
	private SSolutionRow button_row;
	private SSolutionRow status_row;
	
	public SSolutionPane(SSolution solution, SListener1<SSolutionPane> remove_listener) {
		this.solution = solution;
		this.remove_listener = remove_listener;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void runRequest(STestResult result) {
		try { result.run(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void runAllRequest() {
		try { for (STestResult result : results) result.run(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); }
	}
	private void refreshRequest(STestResult result) {
		try { result.refresh(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void refreshAllRequest() {
		try { for (STestResult result : results) result.refresh(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); }
	}
	
//
//  ButtonItem
//
	private class ButtonItem implements SPane {
		private final STestResult result;
		
		private JComponent pane;
		
		public ButtonItem(STestResult result) {
			this.result = result;
			initialize();
		}
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
			SDimension.setButtonItemSize(pane);
			JButton run_button = new JButton(SIcons.runIcon);
			run_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(run_button);
			run_button.setToolTipText("Run");
			run_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					runRequest(result);
				}
			});
			pane.add(run_button);
			JButton refresh_button = new JButton(SIcons.refreshIcon);
			refresh_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(refresh_button);
			refresh_button.setToolTipText("Refresh");
			refresh_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					refreshRequest(result);
				}
			});
			pane.add(refresh_button);
		}
	}
	
//
//  ButtonRow
//
	private class ButtonRow implements SSolutionRow {
		private JComponent pane;
		
		public ButtonRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JPanel label_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
			SDimension.setButtonLabelSize(label_pane);
			JButton run_button = new JButton(SIcons.runIcon);
			run_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(run_button);
			run_button.setToolTipText("Run all");
			run_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					runAllRequest();
				}
			});
			label_pane.add(run_button);
			JButton refresh_button = new JButton(SIcons.refreshIcon);
			refresh_button.setMargin(new Insets(0, 0, 0, 0));
			SDimension.setButtonSize(refresh_button);
			refresh_button.setToolTipText("Refresh all");
			refresh_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					refreshAllRequest();
				}
			});
			label_pane.add(refresh_button);
			pane.add(label_pane);
			pane.add(Box.createHorizontalGlue());
		}
		
		@Override public void addColumn(STestResult result, int index) {
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(new ButtonItem(result).getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			pane.remove(index+1);
		}
	}
	
//
//  StatusItem
//
	private class StatusItem implements SPane, SView {
		private final STestResult result;
		
		private JLabel label;
		private Font normal_font, message_font;
		
		public StatusItem(STestResult result) {
			this.result = result;
			result.addView(this);
			initialize();
		}
		
		@Override public JComponent getPane() { return label; }
		
		private void initialize() {
			label = new JLabel();
			SDimension.setItemSize(label);
			normal_font = label.getFont().deriveFont(Font.PLAIN);
			message_font = label.getFont().deriveFont(Font.BOLD);
			update();
		}
		
		@Override public void update() {
			switch (result.getStatus()) {
			case NOT_TESTED:
				label.setFont(normal_font);
				label.setText("Not tested");
				break;
			case PENDING:
				label.setFont(normal_font);
				label.setText("Pending");
				break;
			case FINISHED:
				label.setFont(message_font);
				label.setText(result.getMessage());
				break;
			}
		}
	}
	
//
//  StatusRow
//
	private class StatusRow implements SSolutionRow {
		private JComponent pane;
		
		public StatusRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JLabel label = new JLabel("Status");
			SDimension.setLabelSize(label);
			pane.add(label);
			pane.add(Box.createHorizontalGlue());
		}
		
		@Override public void addColumn(STestResult result, int index) {
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(new StatusItem(result).getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			pane.remove(index+1);
		}
	}
	
	private void initialize() {
		pane = new Box(BoxLayout.Y_AXIS);
		JPanel solution_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		JLabel solution_label = new JLabel("Solution");
		SDimension.setButtonLabelSize(solution_label);
		solution_pane.add(solution_label);
		solution_input = new SBlobInputView(solution);
		solution_input.setDimension(SDimension.buttonItemDim);
		solution_input.setDescription("Solution file");
		solution.addView(solution_input);
		solution_pane.add(solution_input.getPane());
		JButton remove_button = new JButton(SIcons.removeIcon);
		remove_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(remove_button);
		remove_button.setToolTipText("Remove solution");
		remove_button.setFocusable(false);
		remove_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { remove_listener.call(SSolutionPane.this); }
		});
		solution_pane.add(remove_button);
		pane.add(solution_pane);
		button_row = new ButtonRow();
		pane.add(button_row.getPane());
		status_row = new StatusRow();
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
