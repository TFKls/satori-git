package satori.test;

import java.util.List;
import java.util.ArrayList;
import java.awt.*;
import javax.swing.*;

public class InputRowView implements SRowView {
	private InputMetadata meta;
	private List<SItemView> items;
	
	private JPanel pane;
	private JLabel label;
		
	public InputRowView(InputMetadata meta) {
		this.meta = meta;
		items = new ArrayList<SItemView>();
		initialize();
	}
	
	public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label = new JLabel(meta.getDescription());
		label.setPreferredSize(new Dimension(120, 20));
		label.setFont(label.getFont().deriveFont(Font.PLAIN));
		pane.add(label);
	}
	
	@Override public void addColumn(STestImpl test) {
		addColumn(test, items.size());
	}
	@Override public void addColumn(STestImpl test, int index) {
		SItemView c = meta.createInputView(test.getInput(meta));
		items.add(index, c);
		if (++index >= pane.getComponentCount()) index = -1;
		pane.add(c.getPane(), index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		items.remove(index);
	}
}
