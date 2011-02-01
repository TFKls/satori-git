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
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.SListener;
import satori.common.ui.SPaneView;

public class SButtonRowView implements SRowView {
	private final SItemViewFactory factory;
	private final SListener<STestImpl> new_listener;
	private List<SPaneView> items = new ArrayList<SPaneView>();
	
	private JPanel pane;
	private JLabel label;
	private JButton add_button;
	
	public SButtonRowView(SItemViewFactory factory, SListener<STestImpl> new_listener) {
		this.factory = factory;
		this.new_listener = new_listener;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label = new JLabel();
		label.setPreferredSize(new Dimension(120, 20));
		pane.add(label);
		add_button = new JButton("+");
		add_button.setMargin(new Insets(0, 0, 0, 0));
		add_button.setPreferredSize(new Dimension(24, 20));
		add_button.setToolTipText("Add new test");
		add_button.setFocusable(false);
		add_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { new_listener.call(null); }
		});
		pane.add(add_button);
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		SPaneView c = factory.createView(test);
		items.add(index, c);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		items.remove(index);
	}
}
