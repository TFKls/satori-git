package satori.common.ui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Insets;
import java.awt.Point;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;
import java.awt.event.FocusListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.event.MouseMotionListener;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.StringTokenizer;
import java.util.Vector;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JDialog;
import javax.swing.JFileChooser;
import javax.swing.JList;
import javax.swing.JMenuItem;
import javax.swing.JPanel;
import javax.swing.JPopupMenu;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.ListSelectionModel;
import javax.swing.SwingConstants;
import javax.swing.TransferHandler;

import satori.blob.SBlob;
import satori.common.SInput;
import satori.common.SException;
import satori.main.SFrame;

public class SBlobInputView implements SInputView {
	public static interface BlobLoader {
		Map<String, SBlob> getBlobs() throws SException;
	}
	
	private final SInput<SBlob> data;
	
	private String desc;
	private JComponent pane;
	private JButton clear_button;
	private JButton label;
	private JTextField field;
	private BlobLoader blob_loader = null;
	private boolean edit_mode = false;
	private Font set_font, unset_font;
	private Color default_color;
	
	public SBlobInputView(SInput<SBlob> data) {
		this.data = data;
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	public void setBlobLoader(BlobLoader blob_loader) { this.blob_loader = blob_loader; }
	
	public static class LoadRemoteDialog {
		private final BlobLoader blob_loader;
		private JDialog dialog;
		private JList list;
		private boolean confirmed = false;
		
		public LoadRemoteDialog(BlobLoader blob_loader) {
			this.blob_loader = blob_loader;
			initialize();
		}
		
		private void initialize() {
			dialog = new JDialog(SFrame.get().getFrame(), "Load remote", true);
			dialog.getContentPane().setLayout(new BorderLayout());
			list = new JList();
			list.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
			list.addMouseListener(new MouseAdapter() {
				@Override public void mouseClicked(MouseEvent e) {
					if (e.getClickCount() != 2) return;
					e.consume();
					confirmed = true;
					dialog.setVisible(false);
				}
			});
			JScrollPane list_pane = new JScrollPane(list);
			list_pane.setPreferredSize(new Dimension(200, 100));
			dialog.getContentPane().add(list_pane, BorderLayout.CENTER);			
			JPanel button_pane = new JPanel(new FlowLayout(FlowLayout.CENTER));
			JButton cancel = new JButton("Cancel");
			cancel.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) {
					dialog.setVisible(false);
				}
			});
			button_pane.add(cancel);
			dialog.getContentPane().add(button_pane, BorderLayout.SOUTH);
			dialog.pack();
			dialog.setLocationRelativeTo(SFrame.get().getFrame());
		}
		
		public SBlob process() throws SException {
			Map<String, SBlob> blobs = blob_loader.getBlobs();
			Vector<String> names = new Vector<String>(blobs.keySet());
			Collections.sort(names);
			list.setListData(names);
			dialog.setVisible(true);
			if (!confirmed) return null;
			int index = list.getSelectedIndex();
			if (index == -1) return null;
			return blobs.get(names.get(index));
		}
	}
	
	private void loadRemote() {
		if (blob_loader == null) return;
		LoadRemoteDialog dialog = new LoadRemoteDialog(blob_loader);
		try {
			SBlob blob = dialog.process();
			if (blob == null) return;
			data.set(blob);
		}
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
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
		field.setVisible(true); 
		field.requestFocus();
		label.setVisible(false);
	}
	private void renameDone(boolean focus) {
		if (!edit_mode) return;
		SBlob new_data = data.get().rename(field.getText());
		try { data.set(new_data); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
		edit_mode = false;
		label.setVisible(true);
		if (focus) label.requestFocus();
		field.setVisible(false);
	}
	private void renameCancel() {
		if (!edit_mode) return;
		edit_mode = false;
		label.setVisible(true);
		label.requestFocus();
		field.setVisible(false);
	}
	private void clear() {
		try { data.set(null); }
		catch(SException ex) { SFrame.showErrorDialog(ex); return; }
	}
	
	private Point popup_location = null;
	
	private void showPopup() {
		JPopupMenu popup = new JPopupMenu();
		if (blob_loader != null) {
			JMenuItem loadRemoteItem = new JMenuItem("Load remote");
			loadRemoteItem.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { loadRemote(); }
			});
			popup.add(loadRemoteItem);
		}
		JMenuItem loadItem = new JMenuItem("Load file");
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
		if (popup_location != null) popup.show(label, popup_location.x, popup_location.y);
		else popup.show(label, 0, label.getHeight());
	}
	
	private class LabelListener implements MouseListener, MouseMotionListener {
		@Override public void mousePressed(MouseEvent e) {
			popup_location = e.getPoint();
		}
		@Override public void mouseReleased(MouseEvent e) {
			popup_location = null;
		}
		@Override public void mouseDragged(MouseEvent e) {
			popup_location = null;
			label.getTransferHandler().exportAsDrag(label, e, TransferHandler.COPY);
		}
		@Override public void mouseClicked(MouseEvent e) {}
		@Override public void mouseEntered(MouseEvent e) {}
		@Override public void mouseExited(MouseEvent e) {}
		@Override public void mouseMoved(MouseEvent e) {}
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
				try { data.set(object); }
				catch(SException ex) { SFrame.showErrorDialog(ex); return false; }
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
		pane = new JPanel(null);
		byte[] icon = {71,73,70,56,57,97,7,0,7,0,-128,1,0,-1,0,0,-1,-1,-1,33,-7,4,1,10,0,1,0,44,0,0,0,0,7,0,7,0,0,2,13,12,126,6,-63,-72,-36,30,76,80,-51,-27,86,1,0,59};
		clear_button = new JButton(new ImageIcon(icon));
		clear_button.setMargin(new Insets(0, 0, 0, 0));
		clear_button.setToolTipText("Clear");
		clear_button.setFocusable(false);
		clear_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { clear(); }
		});
		pane.add(clear_button);
		label = new JButton();
		label.setBorder(BorderFactory.createEmptyBorder(0, 1, 0, 1));
		label.setBorderPainted(false);
		label.setContentAreaFilled(false);
		label.setOpaque(false);
		label.setHorizontalAlignment(SwingConstants.LEADING);
		label.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { showPopup(); }
		});
		LabelListener label_listener = new LabelListener();
		label.addMouseListener(label_listener);
		label.addMouseMotionListener(label_listener);
		label.setTransferHandler(new SFileTransferHandler());
		pane.add(label);
		field = new JTextField();
		field.setVisible(false);
		field.addKeyListener(new KeyListener() {
			@Override public void keyPressed(KeyEvent e) {
				if (e.getKeyCode() == KeyEvent.VK_ENTER) {
					e.consume();
					renameDone(true);
				}
				if (e.getKeyCode() == KeyEvent.VK_ESCAPE) {
					e.consume();
					renameCancel();
				}
			}
			@Override public void keyReleased(KeyEvent e) {}
			@Override public void keyTyped(KeyEvent e) {}
		});
		field.addFocusListener(new FocusListener() {
			@Override public void focusGained(FocusEvent e) {}
			@Override public void focusLost(FocusEvent e) { renameDone(false); }
		});
		pane.add(field);
		set_font = label.getFont().deriveFont(Font.PLAIN);
		unset_font = label.getFont().deriveFont(Font.ITALIC);
		default_color = pane.getBackground();
		update();
	}
	
	@Override public void setDimension(Dimension dim) {
		pane.setPreferredSize(dim);
		pane.setMinimumSize(dim);
		pane.setMaximumSize(dim);
		clear_button.setBounds(0, (dim.height-13)/2, 13, 13);
		label.setBounds(15, 0, dim.width-15, dim.height);
		field.setBounds(15, 0, dim.width-15, dim.height);
	}
	@Override public void setDescription(String desc) {
		this.desc = desc;
		update();
		label.setToolTipText(desc);
	}
	
	@Override public void update() {
		pane.setBackground(data.isValid() ? default_color : Color.YELLOW);
		label.setFont(data.get() != null ? set_font : unset_font);
		label.setText(data.get() != null ? data.get().getName() : desc);
	}
}
