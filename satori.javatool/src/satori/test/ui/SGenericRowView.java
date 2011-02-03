package satori.test.ui;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.ui.SPaneView;
import satori.test.impl.STestImpl;

public class SGenericRowView implements SRowView {
	private final String name;
	private final SItemViewFactory factory;
	
	private JComponent pane;
	
	public SGenericRowView(String name, SItemViewFactory factory) {
		this.name = name;
		this.factory = factory;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new Box(BoxLayout.X_AXIS);
		JLabel label = new JLabel(name);
		SDimension.setLabelSize(label);
		pane.add(label);
		pane.add(Box.createHorizontalGlue());
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		SPaneView c = factory.createView(test);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
	}
}
