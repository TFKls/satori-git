package satori.test.ui;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.test.impl.STestImpl;

public class SInfoRowView implements SRowView {
	private JComponent pane;
	
	public SInfoRowView() { initialize(); }
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new Box(BoxLayout.X_AXIS);
		JLabel name_label = new JLabel("Name");
		SDimension.setLabelSize(name_label);
		JLabel judge_label = new JLabel("Judge");
		SDimension.setLabelSize(judge_label);
		Box label_box = new Box(BoxLayout.Y_AXIS);
		label_box.add(name_label);
		label_box.add(judge_label);
		pane.add(label_box);
		pane.add(Box.createHorizontalGlue());
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(new SInfoItemView(test).getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
	}
}
