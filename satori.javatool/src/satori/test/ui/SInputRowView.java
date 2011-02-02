package satori.test.ui;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

import satori.common.ui.SBlobInputView;
import satori.common.ui.SPaneView;
import satori.common.ui.SStringInputView;
import satori.test.impl.SBlobInput;
import satori.test.impl.SStringInput;
import satori.test.impl.STestImpl;
import satori.test.meta.SInputMetadata;

public class SInputRowView implements SRowView {
	private final SInputMetadata meta;
	private List<SPaneView> items = new ArrayList<SPaneView>();
	
	private JPanel pane;
	private JLabel label;
		
	public SInputRowView(SInputMetadata meta) {
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
		SPaneView c;
		if (meta.isBlob()) {
			SBlobInput input = new SBlobInput(meta, test);
			c = new SBlobInputView(input);
		} else {
			SStringInput input = new SStringInput(meta, test);
			c = new SStringInputView(input);
		}
		test.addView(c);
		items.add(index, c);
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(c.getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		items.remove(index);
	}
}
