package satori.test;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Insets;
import java.awt.datatransfer.DataFlavor;
import java.awt.datatransfer.Transferable;
import java.awt.datatransfer.UnsupportedFlavorException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
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
import javax.swing.JPanel;
import javax.swing.TransferHandler;

import satori.common.SFile;
import satori.main.SFrame;

public class SFileInputView implements SItemView {
	private final SFileInputMetadata meta;
	private final SFileInput input;

	private JPanel pane;
	private JButton clear_button;
	private JLabel label;
	private Font set_font, unset_font;
	private Color default_color;
	
	SFileInputView(SFileInputMetadata meta, SFileInput input) {
		this.meta = meta;
		this.input = input;
		input.addView(this);
		initialize();
	}
	
	@Override public JComponent getPane() { return pane; }
	
	private class ButtonListener implements ActionListener {
		@Override public void actionPerformed(ActionEvent e) { input.clearData(); }
	}
	
	private class LabelListener implements MouseListener, MouseMotionListener {
		@Override public void mouseClicked(MouseEvent e) {
			JFileChooser file_chooser = new JFileChooser();
			file_chooser.setSelectedFile(input.getFile());
			int ret = file_chooser.showOpenDialog(SFrame.get().getFrame());
			if (ret != JFileChooser.APPROVE_OPTION) return;
			input.setLocal(file_chooser.getSelectedFile());
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
	
	private static DataFlavor sFileFlavor = new DataFlavor(SFile.class, "Satori file");
	private static DataFlavor stdFileListFlavor = DataFlavor.javaFileListFlavor;
	private static DataFlavor nixFileListFlavor = new DataFlavor("text/uri-list;class=java.lang.String", "Unix file list");
	
	private static class SFileTransferable implements Transferable {
		private final SFile data;
		
		public SFileTransferable(SFile data) { this.data = data; }
		
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
				SFile data;
				try { data = (SFile)t.getTransferData(sFileFlavor); }
				catch(Exception ex) { return false; }
				if (data == null) input.clearData();
				else input.setData(data);
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
			input.setLocal(file_list.get(0));
			return true;
		}
		@Override protected Transferable createTransferable(JComponent c) { return new SFileTransferable(input.getData()); }
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
		label.setTransferHandler(new SFileTransferHandler());
		set_font = label.getFont().deriveFont(Font.PLAIN);
		unset_font = label.getFont().deriveFont(Font.ITALIC);
		default_color = pane.getBackground();
		update();
	}
	
	@Override public void update() {
		switch (input.getStatus()) {
		case VALID:
			pane.setBackground(default_color); break;
		case INVALID:
			pane.setBackground(Color.YELLOW); break;
		case DISABLED:
			pane.setBackground(Color.LIGHT_GRAY); break;
		}
		label.setFont(input.getName() != null ? set_font : unset_font);
		label.setText(input.getName() != null ?
				(input.isRemote() ? "[" + input.getName() + "]" : input.getName()) :
				(input.isRemote() ? "Remote" : "Not set"));
	}
}
