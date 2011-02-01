package satori.common.ui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Insets;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.StringSelection;
import java.awt.datatransfer.Transferable;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.TransferHandler;

import satori.common.SData;

public class SStringInputView implements SPaneView {
	private final SData<String> data;

	private JPanel pane;
	private JButton clear_button;
	private JLabel label;
	private JTextField field;
	private boolean edit_mode = false;
	private Font set_font, unset_font;
	private Color default_color;
	
	public SStringInputView(SData<String> data) {
		this.data = data;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private class ButtonListener implements ActionListener {
		@Override public void actionPerformed(ActionEvent e) { data.set(null); }
	}
	
	private class LabelListener implements MouseListener, MouseMotionListener {
		@Override public void mouseClicked(MouseEvent e) {
			edit_mode = true;
			field.setText(data.get());
			field.selectAll();
			label.setVisible(false);
			field.setVisible(true); 
			field.requestFocus();
		}
		@Override public void mouseDragged(MouseEvent e) {
			label.getTransferHandler().exportAsDrag(label, e, TransferHandler.COPY);
		}
		@Override public void mouseEntered(MouseEvent e) {}
		@Override public void mouseExited(MouseEvent e) {}
		@Override public void mouseMoved(MouseEvent e) {}
		@Override public void mousePressed(MouseEvent e) {}
		@Override public void mouseReleased(MouseEvent e) {}
	}
	
	private class FieldListener implements ActionListener, FocusListener {
		@Override public void actionPerformed(ActionEvent e) {
			edit_mode = false;
			if (field.getText().isEmpty()) data.set(null);
			else data.set(field.getText());
			field.setVisible(false);
			label.setVisible(true); 
		}
		@Override public void focusGained(FocusEvent e) {}
		@Override public void focusLost(FocusEvent e) {
			if (!edit_mode) return;
			edit_mode = false;
			field.setVisible(false);
			label.setVisible(true); 
		}
	}
	
	private class LabelTransferHandler extends TransferHandler {
		@Override public boolean canImport(TransferSupport support) {
			if (!support.isDataFlavorSupported(DataFlavor.stringFlavor)) return false;
			if ((support.getSourceDropActions() & COPY) == COPY) {
				support.setDropAction(COPY);
				return true;
			}
			return false;
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
			Transferable t = support.getTransferable();
			String object;
			try { object = (String)t.getTransferData(DataFlavor.stringFlavor); }
			catch (Exception e) { return false; }
			if (object == null || object.isEmpty()) data.set(null);
			else data.set(object);
			return true;
		}
		@Override protected Transferable createTransferable(JComponent c) { return new StringSelection(data.get()); }
		@Override public int getSourceActions(JComponent c) { return COPY; }
		@Override protected void exportDone(JComponent source, Transferable data, int action) {}
	}
	
	private void initialize() {
		pane = new JPanel();
		pane.setLayout(null);
		pane.setPreferredSize(new Dimension(120, 20));
		byte[] icon = {71,73,70,56,57,97,7,0,7,0,-128,1,0,-1,0,0,-1,-1,-1,33,-7,4,1,10,0,1,0,44,0,0,0,0,7,0,7,0,0,2,13,12,126,6,-63,-72,-36,30,76,80,-51,-27,86,1,0,59};
		clear_button = new JButton(new ImageIcon(icon));
		clear_button.setMargin(new Insets(0, 0, 0, 0));
		pane.add(clear_button);
		clear_button.setBounds(4, 4, 13, 13);
		clear_button.setActionCommand("clear");
		clear_button.addActionListener(new ButtonListener());
		label = new JLabel();
		pane.add(label);
		label.setBounds(20, 0, 100, 20);
		LabelListener label_listener = new LabelListener();
		label.addMouseListener(label_listener);
		label.addMouseMotionListener(label_listener);
		label.setTransferHandler(new LabelTransferHandler());
		field = new JTextField();
		field.setVisible(false);
		pane.add(field);
		field.setBounds(20, 0, 100, 20);
		field.setActionCommand("accept");
		FieldListener field_listener = new FieldListener();
		field.addActionListener(field_listener);
		field.addFocusListener(field_listener);
		set_font = label.getFont().deriveFont(Font.PLAIN);
		unset_font = label.getFont().deriveFont(Font.ITALIC);
		default_color = pane.getBackground();
		update();
	}
	
	@Override public void update() {
		if (data.isEnabled()) pane.setBackground(data.isValid() ? default_color : Color.YELLOW);
		else pane.setBackground(Color.LIGHT_GRAY);
		label.setFont(data.get() != null ? set_font : unset_font);
		label.setText(data.get() != null ? data.get() : "Not set");
	}
}
