package satori.test.ui;

import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.SListener;
import satori.common.ui.SPaneView;
import satori.test.impl.STestImpl;

public class SButtonRowView implements SRowView {
	private final SItemViewFactory factory;
	private final SListener<STestImpl> new_listener;
	
	private JComponent pane;
	
	public SButtonRowView(SItemViewFactory factory, SListener<STestImpl> new_listener) {
		this.factory = factory;
		this.new_listener = new_listener;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new Box(BoxLayout.X_AXIS);
		JLabel label = new JLabel();
		SDimension.setButtonLabelSize(label);
		pane.add(label);
		JButton add_button = new JButton(SIcons.addIcon);
		add_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(add_button);
		add_button.setToolTipText("Add new test");
		add_button.setFocusable(false);
		add_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { new_listener.call(null); }
		});
		pane.add(add_button);
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
