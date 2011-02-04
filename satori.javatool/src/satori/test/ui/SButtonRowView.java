package satori.test.ui;

import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;

import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;

import satori.common.SListener1;
import satori.common.SListener0;
import satori.common.SListener2;
import satori.test.impl.STestImpl;

public class SButtonRowView implements SRowView {
	private final SListener2<STestImpl, MouseEvent> move_listener;
	private final SListener1<STestImpl> remove_listener;
	private final SListener0 add_listener;
	
	private JComponent pane;
	
	public SButtonRowView(SListener2<STestImpl, MouseEvent> move_listener, SListener1<STestImpl> remove_listener, SListener0 add_listener) {
		this.move_listener = move_listener;
		this.remove_listener = remove_listener;
		this.add_listener = add_listener;
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
		add_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { add_listener.call(); }
		});
		pane.add(add_button);
		pane.add(Box.createHorizontalGlue());
	}
	
	@Override public void addColumn(STestImpl test, int index) {
		int pane_index = (index+1 < pane.getComponentCount()) ? index+1 : -1;
		pane.add(new SButtonItemView(test, move_listener, remove_listener).getPane(), pane_index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
	}
}
