package satori.test;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;

import satori.common.SException;
import satori.common.SListener;
import satori.main.SFrame;

public class SButtonItemView implements SItemView {
	private final STestImpl test;
	private final SListener<STestImpl> close_listener;
	
	private JPanel pane;
	private JButton save_button, reload_button, delete_button, close_button;
	
	public SButtonItemView(STestImpl test, SListener<STestImpl> close_listener) {
		this.test = test;
		this.close_listener = close_listener;
		test.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private boolean askUnsaved() { return SFrame.showWarningDialog("All unsaved changes to the test will be lost."); }
	
	private void saveRequest() {
		try { if (test.isRemote()) test.save(); else test.create(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void reloadRequest() {
		if (!test.isRemote()) return;
		if (test.isModified() && !askUnsaved()) return;
		try { test.reload(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void deleteRequest() {
		if (!test.isRemote()) return;
		if (!SFrame.showWarningDialog("The test will be deleted.")) return;
		try { test.delete(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void closeRequest() {
		if (test.isModified() && !askUnsaved()) return;
		close_listener.call(test);
		test.close();
	}
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(new FlowLayout(FlowLayout.LEFT, 0, 0));
		save_button = new JButton("S");
		save_button.setMargin(new Insets(0, 0, 0, 0));
		save_button.setPreferredSize(new Dimension(30, 25));
		save_button.setToolTipText("Save");
		save_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { saveRequest(); }
		});
		pane.add(save_button);
		reload_button = new JButton("R");
		reload_button.setMargin(new Insets(0, 0, 0, 0));
		reload_button.setPreferredSize(new Dimension(30, 25));
		reload_button.setToolTipText("Reload");
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		pane.add(reload_button);
		delete_button = new JButton("D");
		delete_button.setMargin(new Insets(0, 0, 0, 0));
		delete_button.setPreferredSize(new Dimension(30, 25));
		delete_button.setToolTipText("Delete");
		delete_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { deleteRequest(); }
		});
		pane.add(delete_button);
		close_button = new JButton("X");
		close_button.setMargin(new Insets(0, 0, 0, 0));
		close_button.setPreferredSize(new Dimension(30, 25));
		close_button.setToolTipText("Close");
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeRequest(); }
		});
		pane.add(close_button);
		update();
	}
	
	@Override public void update() {}
	
	public static class Factory implements SItemViewFactory {
		public final SListener<STestImpl> close_listener;
		public Factory(SListener<STestImpl> close_listener) {
			this.close_listener = close_listener;
		}
		@Override public SItemView createView(STestImpl test) {
			return new SButtonItemView(test, close_listener);
		}
	}
}
