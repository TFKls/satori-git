package satori.test.ui;

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
import satori.common.SListener1;
import satori.common.SListener2;
import satori.common.ui.SPaneView;
import satori.main.SFrame;
import satori.test.impl.STestImpl;

public class SButtonItemView implements SPaneView {
	private final STestImpl test;
	private final SListener1<STestImpl> remove_listener;
	private final SListener2<STestImpl, MouseEvent> move_listener;
	
	private JPanel pane;
	private JButton move_button, save_button, reload_button, delete_button, remove_button;
	
	public SButtonItemView(STestImpl test, SListener2<STestImpl, MouseEvent> move_listener, SListener1<STestImpl> remove_listener) {
		this.test = test;
		this.move_listener = move_listener;
		this.remove_listener = remove_listener;
		test.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void saveRequest() {
		if (!test.isProblemRemote()) { SFrame.showErrorDialog("Cannot save: the problem does not exist remotely"); return; }
		try { if (test.isRemote()) test.save(); else test.create(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void reloadRequest() {
		if (!test.isRemote()) return;
		try { test.reload(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void deleteRequest() {
		if (!test.isRemote()) return;
		if (!SFrame.showWarningDialog("The test will be deleted.")) return;
		try { test.delete(); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void removeRequest() {
		if (test.isModified() && !SFrame.showWarningDialog("The test contains unsaved data.")) return;
		test.close();
		remove_listener.call(test);
	}
	
	private void initialize() {
		pane = new JPanel(new FlowLayout(FlowLayout.LEFT, 0, 0));
		SDimension.setButtonItemSize(pane);
		move_button = new JButton(SIcons.moveIcon);
		move_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(move_button);
		move_button.setToolTipText("Move");
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
		save_button = new JButton(SIcons.saveIcon);
		save_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(save_button);
		save_button.setToolTipText("Save");
		save_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { saveRequest(); }
		});
		pane.add(save_button);
		reload_button = new JButton(SIcons.refreshIcon);
		reload_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(reload_button);
		reload_button.setToolTipText("Reload");
		reload_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { reloadRequest(); }
		});
		pane.add(reload_button);
		delete_button = new JButton(SIcons.trashIcon);
		delete_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(delete_button);
		delete_button.setToolTipText("Delete");
		delete_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { deleteRequest(); }
		});
		pane.add(delete_button);
		remove_button = new JButton(SIcons.removeIcon);
		remove_button.setMargin(new Insets(0, 0, 0, 0));
		SDimension.setButtonSize(remove_button);
		remove_button.setToolTipText("Remove");
		remove_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { removeRequest(); }
		});
		pane.add(remove_button);
		update();
	}
	
	@Override public void update() {}
}
