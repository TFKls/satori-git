package satori.test.ui;

import java.util.ArrayList;
import java.util.List;

import javax.swing.BoxLayout;
import javax.swing.JComponent;
import javax.swing.JPanel;

import satori.test.impl.STestImpl;

public class STestInputPane implements SRowView {
	private List<SRowView> rows = new ArrayList<SRowView>();
	
	private JPanel pane;
	
	public STestInputPane() { initialize(); }
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new BoxLayout(pane, BoxLayout.Y_AXIS));
	}
		
	public void addRow(SRowView row) {
		rows.add(row);
		pane.add(row.getPane());
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		for (SRowView row : rows) row.addColumn(test, index);
	}
	@Override public void removeColumn(int index) {
		for (SRowView row : rows) row.removeColumn(index);
	}
}
