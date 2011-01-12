package satori.test;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.List;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;

public class SButtonRowView implements SRowView {
	public interface NewCallback { void call(); }
	
	private final SItemViewFactory factory;
	private final NewCallback new_callback;
	private List<SItemView> items = new ArrayList<SItemView>();
	
	private JPanel pane;
	private JLabel label;
	private JButton add_button;
	
	SButtonRowView(SItemViewFactory factory, NewCallback new_callback) {
		this.factory = factory;
		this.new_callback = new_callback;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		label = new JLabel();
		label.setPreferredSize(new Dimension(120, 25));
		pane.add(label);
		add_button = new JButton("+");
		add_button.setMargin(new Insets(0, 0, 0, 0));
		add_button.setPreferredSize(new Dimension(30, 25));
		add_button.setToolTipText("Add new test");
		add_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { new_callback.call(); }
		});
		pane.add(add_button);
	}
	
	@Override public void addColumn(STestImpl test) {
		addColumn(test, items.size());
	}
	@Override public void addColumn(STestImpl test, int index) {
		SItemView c = factory.createView(test);
		items.add(index, c);
		if (++index >= pane.getComponentCount()) index = -1;
		pane.add(c.getPane(), index);
	}
	@Override public void removeColumn(int index) {
		pane.remove(index+1);
		//pane.invalidate(); pane.repaint();
		items.remove(index);
	}
}
