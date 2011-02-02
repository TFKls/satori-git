package satori.test.ui;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.ui.SPaneView;
import satori.test.impl.STestImpl;
import satori.test.meta.InputMetadata;

public class InputRowView implements SRowView {
	private final InputMetadata meta;
	private List<SPaneView> items = new ArrayList<SPaneView>();
	
	private JPanel pane;
	private JLabel label;
		
	public InputRowView(InputMetadata meta) {
		this.meta = meta;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label = new JLabel(meta.getDescription());
		label.setPreferredSize(new Dimension(120, 20));
		label.setFont(label.getFont().deriveFont(Font.PLAIN));
		pane.add(label);
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		SPaneView c = meta.createInputView(test.getInput(meta));
		items.add(index, c);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		items.remove(index);
	}
}
