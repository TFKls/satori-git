package satori.test;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.awt.event.MouseMotionListener;

import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JPanel;

import satori.common.SException;
import satori.common.SListener;
import satori.common.SListener2;
import satori.common.ui.SPaneView;
import satori.main.SFrame;

public class SButtonItemView implements SPaneView {
	private final STestImpl test;
	private final SListener<STestImpl> close_listener;
	private final SListener2<STestImpl, MouseEvent> move_listener;

	private JPanel pane;
	private JButton move_button, save_button, reload_button, delete_button, close_button;
	
	public SButtonItemView(STestImpl test, SListener2<STestImpl, MouseEvent> move_listener, SListener<STestImpl> close_listener) {
		this.test = test;
		this.move_listener = move_listener;
		this.close_listener = close_listener;
		test.addView(this); //TODO
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
		move_button = new JButton("M");
		move_button.setMargin(new Insets(0, 0, 0, 0));
		move_button.setPreferredSize(new Dimension(24, 25));
		move_button.setToolTipText("Move");
		move_button.setFocusable(false);
		move_button.addMouseMotionListener(new MouseMotionListener() {
			@Override public void mouseDragged(MouseEvent e) {
				move_button.getModel().setArmed(false);
				move_button.getModel().setPressed(false);
				move_button.getModel().setRollover(false);
				move_listener.call(test, e);
			}
			@Override public void mouseMoved(MouseEvent e) {}
		});
		pane.add(move_button);
		save_button = new JButton("S");
		save_button.setMargin(new Insets(0, 0, 0, 0));
		save_button.setPreferredSize(new Dimension(24, 25));
		save_button.setToolTipText("Save");
		save_button.setFocusable(false);
		save_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { saveRequest(); }
		});
		pane.add(save_button);
		reload_button = new JButton("R");
		reload_button.setMargin(new Insets(0, 0, 0, 0));
		reload_button.setPreferredSize(new Dimension(24, 25));
		reload_button.setToolTipText("Reload");
		reload_button.setFocusable(false);
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		pane.add(reload_button);
		delete_button = new JButton("D");
		delete_button.setMargin(new Insets(0, 0, 0, 0));
		delete_button.setPreferredSize(new Dimension(24, 25));
		delete_button.setToolTipText("Delete");
		delete_button.setFocusable(false);
		delete_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { deleteRequest(); }
		});
		pane.add(delete_button);
		close_button = new JButton("X");
		close_button.setMargin(new Insets(0, 0, 0, 0));
		close_button.setPreferredSize(new Dimension(24, 25));
		close_button.setToolTipText("Close");
		close_button.setFocusable(false);
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeRequest(); }
		});
		pane.add(close_button);
		update();
	}
	
	@Override public void update() {}
	
	public static class Factory implements SItemViewFactory {
		public final SListener2<STestImpl, MouseEvent> move_listener;
		public final SListener<STestImpl> close_listener;
		public Factory(SListener2<STestImpl, MouseEvent> move_listener, SListener<STestImpl> close_listener) {
			this.move_listener = move_listener;
			this.close_listener = close_listener;
		}
		@Override public SPaneView createView(STestImpl test) {
			return new SButtonItemView(test, move_listener, close_listener);
		}
	}
}
