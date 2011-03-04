package satori.test.ui;

import java.awt.Color;
import java.awt.FlowLayout;
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
import satori.common.SListener0;
import satori.common.SListener1;
import satori.common.SView;
import satori.common.ui.SBlobInputView;
import satori.common.ui.SBlobOutputView;
import satori.common.ui.SPaneView;
import satori.common.ui.SPane;
import satori.common.ui.SStringOutputView;
import satori.main.SFrame;
import satori.metadata.SOutputMetadata;
import satori.test.impl.SBlobOutput;
import satori.test.impl.SSolution;
import satori.test.impl.SStringOutput;
import satori.test.impl.STestImpl;
import satori.test.impl.STestResult;
import satori.type.SBlobType;

public class SSolutionPane implements SRow {
	private final SSolution solution;
	private final SListener1<SSolutionPane> remove_listener;
	private final List<STestResult> results = new ArrayList<STestResult>();
	
	private JComponent pane;
	private SBlobInputView solution_input;
	private SSolutionRow button_row;
	private ResultRow result_row;
	
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
//  ResultItem
//
	private class ResultItem implements SPane, SView {
		private final STestResult result;
		
		private JComponent pane;
		private Color default_color;
		
		private final SListener0 meta_listener = new SListener0() {
			@Override public void call() {
				pane.removeAll();
				fillPane();
				pane.revalidate(); pane.repaint();
			}
		};
		
		public ResultItem(STestResult result) {
			this.result = result;
			result.addView(this);
			initialize();
		}
		
		@Override public JComponent getPane() { return pane; }
		
		private void fillPane() {
			for (SOutputMetadata om : result.getTest().getOutputMetadata()) {
				SPaneView view;
				if (om.getType() == SBlobType.INSTANCE) view = new SBlobOutputView(new SBlobOutput(om, result));
				else view = new SStringOutputView(new SStringOutput(om, result));
				result.addView(view);
				view.getPane().setPreferredSize(SDimension.itemDim);
				view.getPane().setMinimumSize(SDimension.itemDim);
				view.getPane().setMaximumSize(SDimension.itemDim);
				pane.add(view.getPane());
			}
			pane.add(Box.createVerticalGlue());
		}
		private void initialize() {
			pane = new Box(BoxLayout.Y_AXIS);
			pane.setOpaque(true);
			fillPane();
			result.getTest().addMetadataModifiedListener(meta_listener);
			default_color = pane.getBackground();
		}
		
		public void close() {
			result.getTest().removeMetadataModifiedListener(meta_listener);
		}
		
		@Override public void update() {
			switch (result.getStatus()) {
			case NOT_TESTED:
				pane.setBackground(default_color); break;
			case PENDING:
				pane.setBackground(Color.YELLOW); break;
			case FINISHED:
				pane.setBackground(Color.GREEN); break;
			}
		}
	}
	
//
//  ResultRow
//
	private class ResultRow implements SSolutionRow {
		private List<ResultItem> items = new ArrayList<ResultItem>();
		private JComponent pane;
		
		public ResultRow() { initialize(); }
		
		@Override public JComponent getPane() { return pane; }
		
		private void initialize() {
			pane = new Box(BoxLayout.X_AXIS);
			JLabel label = new JLabel("Result");
			SDimension.setLabelSize(label);
			Box label_box = new Box(BoxLayout.Y_AXIS);
			label_box.add(label);
			label_box.add(Box.createVerticalGlue());
			pane.add(label_box);
			pane.add(Box.createHorizontalGlue());
		}
		
		public void close() { for (ResultItem item : items) item.close(); }
		
		@Override public void addColumn(STestResult result, int index) {
			ResultItem item = new ResultItem(result);
			items.add(index, item);
			int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
			pane.add(item.getPane(), pane_index);
		}
		@Override public void removeColumn(int index) {
			//items.get(index).close(); // TODO: necessary?
			items.remove(index);
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
		solution.addView(solution_input);
		solution_input.getPane().setPreferredSize(SDimension.buttonItemDim);
		solution_input.getPane().setMinimumSize(SDimension.buttonItemDim);
		solution_input.getPane().setMaximumSize(SDimension.buttonItemDim);
		solution_pane.add(solution_input.getPane());
		JButton remove_button = new JButton(SIcons.removeIcon);
		remove_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(remove_button);
		remove_button.setToolTipText("Remove solution");
		remove_button.setFocusable(false);
		remove_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				result_row.close();
				remove_listener.call(SSolutionPane.this);
			}
		});
		solution_pane.add(remove_button);
		pane.add(solution_pane);
		button_row = new ButtonRow();
		pane.add(button_row.getPane());
		result_row = new ResultRow();
		pane.add(result_row.getPane());
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		STestResult result = new STestResult(solution, test);
		results.add(index, result);
		button_row.addColumn(result, index);
		result_row.addColumn(result, index);
	}
	@Override public void removeColumn(int index) {
		button_row.removeColumn(index);
		result_row.removeColumn(index);
		results.get(index).close();
		results.remove(index);
	}
}
