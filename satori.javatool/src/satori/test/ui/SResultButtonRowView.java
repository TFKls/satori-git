package satori.test.ui;

import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;

import satori.common.SListener0;
import satori.test.impl.STestResult;

public class SResultButtonRowView implements SSolutionRowView {
	private final SListener0 run_all_listener;
	private final SListener0 refresh_all_listener;
	
	private JComponent pane;
	
	public SResultButtonRowView(SListener0 run_all_listener, SListener0 refresh_all_listener) {
		this.run_all_listener = run_all_listener;
		this.refresh_all_listener = refresh_all_listener;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new Box(BoxLayout.X_AXIS);
		JPanel label_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		SDimension.setLabelSize(label_pane);
		JButton run_button = new JButton("Run");
		run_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setHeight(run_button);
		run_button.setFocusable(false);
		run_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { run_all_listener.call(); }
		});
		label_pane.add(run_button);
		JButton refresh_button = new JButton("Refresh");
		refresh_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setHeight(refresh_button);
		refresh_button.setFocusable(false);
		refresh_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { refresh_all_listener.call(); }
		});
		label_pane.add(refresh_button);
		pane.add(label_pane);
		pane.add(Box.createHorizontalGlue());
	}
	
	@Override public void addColumn(STestResult result, int index) {
		SResultButtonItemView c = new SResultButtonItemView(result);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
	}
}
