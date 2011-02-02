package satori.test.ui;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.test.impl.STestResult;

public class SResultStatusRowView implements SSolutionRowView {
	private List<SResultStatusItemView> items = new ArrayList<SResultStatusItemView>();
	
	private JPanel pane;
	
	public SResultStatusRowView() { initialize(); }
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		JLabel label = new JLabel("Status");
		label.setPreferredSize(new Dimension(120, 20));
		label.setFont(label.getFont().deriveFont(Font.PLAIN));
		pane.add(label);
	}
	
	@Override public void addColumn(STestResult result, int index) {
		SResultStatusItemView c = new SResultStatusItemView(result);
		items.add(index, c);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		items.remove(index);
	}
}
