package satori.test;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;

import satori.common.SListener0;

public class SResultButtonRowView implements SSolutionRowView {
	private final List<SResultButtonItemView> items = new ArrayList<SResultButtonItemView>();
	private final SListener0 run_all_listener;
	private final SListener0 refresh_all_listener;
	
	private JPanel pane;
	private JPanel label_pane;
	private JButton run_button, refresh_button;
	
	public SResultButtonRowView(SListener0 run_all_listener, SListener0 refresh_all_listener) {
		this.run_all_listener = run_all_listener;
		this.refresh_all_listener = refresh_all_listener;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label_pane = new JPanel();
		label_pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		run_button = new JButton("Run");
		run_button.setMargin(new Insets(0, 0, 0, 0));
		run_button.setPreferredSize(new Dimension(50, 20));
		run_button.setFocusable(false);
		run_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { run_all_listener.call(); }
		});
		label_pane.add(run_button);
		refresh_button = new JButton("Refresh");
		refresh_button.setMargin(new Insets(0, 0, 0, 0));
		refresh_button.setPreferredSize(new Dimension(70, 20));
		refresh_button.setFocusable(false);
		refresh_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { refresh_all_listener.call(); }
		});
		label_pane.add(refresh_button);
		pane.add(label_pane);
	}
	
	@Override public void addColumn(STestResult result, int index) {
		SResultButtonItemView c = new SResultButtonItemView(result);
		items.add(index, c);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		items.remove(index);
	}
}
