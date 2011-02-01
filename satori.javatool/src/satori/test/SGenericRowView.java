package satori.test;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.ui.SPaneView;

public class SGenericRowView implements SRowView {
	private final String name;
	private final SItemViewFactory factory;
	private List<SPaneView> items = new ArrayList<SPaneView>();
	
	private JPanel pane;
	private JLabel label;
	
	public SGenericRowView(String name, SItemViewFactory factory) {
		this.name = name;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label = new JLabel(name);
		label.setPreferredSize(new Dimension(120, 20));
		pane.add(label);
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
