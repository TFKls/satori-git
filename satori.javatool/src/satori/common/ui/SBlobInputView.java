package satori.common.ui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Insets;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.StringTokenizer;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JTextField;
import javax.swing.TransferHandler;

import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SException;
import satori.main.SFrame;

public class SBlobInputView implements SPaneView {
	private final SData<SBlob> data;
	
	private JPanel pane;
	private JButton clear_button;
	private JLabel label;
	private JTextField field;
	private boolean edit_mode = false;
	private Font set_font, unset_font;
	private Color default_color;
	
	public SBlobInputView(SData<SBlob> data) {
		this.data = data;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private void loadFile() {
		JFileChooser file_chooser = new JFileChooser();
		file_chooser.setSelectedFile(data.get() != null ? data.get().getFile() : null);
		int ret = file_chooser.showDialog(SFrame.get().getFrame(), "Load");
		if (ret != JFileChooser.APPROVE_OPTION) return;
		try { data.set(SBlob.createLocal(file_chooser.getSelectedFile())); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void saveFile() {
		if (data.get() == null) return;
		JFileChooser file_chooser = new JFileChooser();
		String name = data.get().getName();
		if (name != null && !name.isEmpty()) file_chooser.setSelectedFile(new File(file_chooser.getCurrentDirectory(), name));
		int ret = file_chooser.showDialog(SFrame.get().getFrame(), "Save");
		if (ret != JFileChooser.APPROVE_OPTION) return;
		try { data.get().saveLocal(file_chooser.getSelectedFile()); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	private void rename() {
		if (edit_mode || data.get() == null) return;
		edit_mode = true;
		field.setText(data.get().getName());
		field.selectAll();
		label.setVisible(false);
		field.setVisible(true); 
		field.requestFocus();
	}
	private void renameDone() {
		if (!edit_mode) return;
		edit_mode = false;
		data.set(data.get().rename(field.getText()));
		field.setVisible(false);
		label.setVisible(true); 
	}
	
	private class ButtonListener implements ActionListener {
		@Override public void actionPerformed(ActionEvent e) { data.set(null); }
	}
	
	private class LabelListener implements MouseListener, MouseMotionListener {
		@Override public void mouseClicked(MouseEvent e) {
			JPopupMenu popup = new JPopupMenu();
			JMenuItem loadItem = new JMenuItem("Load");
			loadItem.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { loadFile(); }
			});
			popup.add(loadItem);
			JMenuItem saveItem = new JMenuItem("Save");
			saveItem.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { saveFile(); }
			});
			popup.add(saveItem);
			JMenuItem renameItem = new JMenuItem("Rename");
			renameItem.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { rename(); }
			});
			popup.add(renameItem);
			popup.show(e.getComponent(), e.getX(), e.getY());
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
		@Override public void actionPerformed(ActionEvent e) { renameDone(); }
		@Override public void focusGained(FocusEvent e) {}
		@Override public void focusLost(FocusEvent e) { renameDone(); }
	}
	
	private static DataFlavor sFileFlavor = new DataFlavor(SBlob.class, "Satori file");
	private static DataFlavor stdFileListFlavor = DataFlavor.javaFileListFlavor;
	private static DataFlavor nixFileListFlavor = new DataFlavor("text/uri-list;class=java.lang.String", "Unix file list");
	
	private static class SFileTransferable implements Transferable {
		private final SBlob data;
		
		public SFileTransferable(SBlob data) { this.data = data; }
		
		@Override public DataFlavor[] getTransferDataFlavors() {
			DataFlavor[] flavors = new DataFlavor[1];
			flavors[0] = sFileFlavor;
			return flavors;
		}
		@Override public boolean isDataFlavorSupported(DataFlavor flavor) {
			return flavor.match(sFileFlavor);
		}
		@Override public Object getTransferData(DataFlavor flavor) throws UnsupportedFlavorException, IOException {
			if (flavor.match(sFileFlavor)) return data;
			else throw new UnsupportedFlavorException(flavor);
		}
	}
	
	@SuppressWarnings("unchecked")
	private static List<File> importStdFileList(Object obj) {
		try { return (List<File>)obj; }
		catch(Exception ex) { return null; }
	}
	private static List<File> importNixFileList(Object obj) {
		String data;
		try { data = (String)obj; }
		catch(Exception ex) { return null; }
		List<File> list = new ArrayList<File>();
		for (StringTokenizer st = new StringTokenizer(data, "\r\n"); st.hasMoreTokens();) {
			String token = st.nextToken().trim();
			if (token.isEmpty() || token.startsWith("#")) continue;
			File file;
			try { file = new File(new URI(token)); }
			catch(Exception ex) { return null; }
			list.add(file);
		}
		return list;
	}
	
	@SuppressWarnings("serial")
	private class SFileTransferHandler extends TransferHandler {
		@Override public boolean canImport(TransferSupport support) {
			if ((support.getSourceDropActions() & COPY) != COPY) return false;
			support.setDropAction(COPY);
			if (support.isDataFlavorSupported(sFileFlavor)) return true;
			if (support.isDataFlavorSupported(stdFileListFlavor)) return true;
			if (support.isDataFlavorSupported(nixFileListFlavor)) return true;
			return false;
		}
		@Override public boolean importData(TransferSupport support) {
			if (!support.isDrop()) return false;
			Transferable t = support.getTransferable();
			if (support.isDataFlavorSupported(sFileFlavor)) {
				SBlob object;
				try { object = (SBlob)t.getTransferData(sFileFlavor); }
				catch(Exception ex) { return false; }
				data.set(object);
				return true;
			}
			List<File> file_list = null;
			try {
				if (support.isDataFlavorSupported(stdFileListFlavor))
					file_list = importStdFileList(t.getTransferData(stdFileListFlavor));
				else if (support.isDataFlavorSupported(nixFileListFlavor))
					file_list = importNixFileList(t.getTransferData(nixFileListFlavor));
			}
			catch(Exception ex) { return false; }
			if (file_list == null || file_list.size() != 1) return false;
			try { data.set(SBlob.createLocal(file_list.get(0))); }
			catch(SException ex) { SFrame.showErrorDialog(ex); return false; }
			return true;
		}
		@Override protected Transferable createTransferable(JComponent c) { return new SFileTransferable(data.get()); }
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
		clear_button.addActionListener(new ButtonListener());
		label = new JLabel();
		pane.add(label);
		label.setBounds(20, 0, 100, 20);
		LabelListener label_listener = new LabelListener();
		label.addMouseListener(label_listener);
		label.addMouseMotionListener(label_listener);
		label.setTransferHandler(new SFileTransferHandler());
		field = new JTextField();
		field.setVisible(false);
		pane.add(field);
		field.setBounds(20, 0, 100, 20);
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
		SBlob file = data.get();
		label.setFont(file != null ? set_font : unset_font);
		label.setText(file != null ? file.getName() : "Not set");
	}
}
