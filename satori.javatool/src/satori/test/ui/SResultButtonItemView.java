package satori.test.ui;

import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;

import satori.common.SException;
import satori.common.ui.SPaneView;
import satori.main.SFrame;
import satori.test.impl.STestResult;

public class SResultButtonItemView implements SPaneView {
	private final STestResult result;
	
	private JComponent pane;
	
	public SResultButtonItemView(STestResult result) {
		this.result = result;
		result.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void runRequest() {
		try { result.run(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void refreshRequest() {
		try { result.refresh(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	
	private void initialize() {
		pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		SDimension.setItemSize(pane);
		JButton run_button = new JButton("Run");
		run_button.setMargin(new Insets(0, 0, 0, 0));
		run_button.setFocusable(false);
		SDimension.setHeight(run_button);
		run_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { runRequest(); }
		});
		pane.add(run_button);
		JButton refresh_button = new JButton("Refresh");
		refresh_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setHeight(refresh_button);
		refresh_button.setFocusable(false);
		refresh_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { refreshRequest(); }
		});
		pane.add(refresh_button);
		update();
	}
	
	@Override public void update() {}
}
