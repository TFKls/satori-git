package satori.common.ui;

import java.awt.FlowLayout;

import javax.swing.JComponent;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.border.EmptyBorder;

public class SScrollPane implements SPane {
	private JScrollPane pane;
	private JPanel inner_pane;
	private JComponent view;
	
	public SScrollPane() { initialize(); }
	
	@Override public JComponent getPane() { return pane; }
	
	private void initialize() {
		inner_pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		pane = new JScrollPane(inner_pane);
		pane.setBorder(new EmptyBorder(0, 0, 0, 0));
	}
	
	public void setView(JComponent view) {
		if (this.view != null) inner_pane.remove(this.view);
		this.view = view;
		if (this.view != null) inner_pane.add(this.view);
	}
}
