package satori.common.ui;

import java.awt.Dimension;
import java.awt.Font;
import java.awt.Point;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.io.File;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JFileChooser;
import javax.swing.JMenuItem;
import javax.swing.JPopupMenu;
import javax.swing.SwingConstants;

import satori.blob.SBlob;
import satori.common.SData;
import satori.common.SException;
import satori.main.SFrame;

public class SBlobOutputView implements SInputView {
	private final SData<SBlob> data;
	
	private String desc;
	private JButton label;
	private Font set_font, unset_font;
	
	public SBlobOutputView(SData<SBlob> data) {
		this.data = data;
		initialize();
	}
	
	@Override public JComponent getPane() { return label; }
	
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
	
	private void showPopup(Point location) {
		JPopupMenu popup = new JPopupMenu();
		JMenuItem saveItem = new JMenuItem("Save");
		saveItem.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { saveFile(); }
		});
		popup.add(saveItem);
		if (location != null) popup.show(label, location.x, location.y);
		else popup.show(label, 0, label.getHeight());
	}
	
	private void initialize() {
		label = new JButton();
		label.setBorder(BorderFactory.createEmptyBorder(0, 1, 0, 1));
		label.setBorderPainted(false);
		label.setContentAreaFilled(false);
		label.setOpaque(false);
		label.setHorizontalAlignment(SwingConstants.LEADING);
		label.addMouseListener(new MouseAdapter() {
			@Override public void mouseClicked(MouseEvent e) { showPopup(e.getPoint()); }
		});
		label.addKeyListener(new KeyAdapter() {
			@Override public void keyPressed(KeyEvent e) {
				if (e.getKeyCode() == KeyEvent.VK_ENTER) { e.consume(); showPopup(null); }
			}
		});
		set_font = label.getFont().deriveFont(Font.PLAIN);
		unset_font = label.getFont().deriveFont(Font.ITALIC);
		update();
	}
	
	@Override public void setDimension(Dimension dim) {
		label.setPreferredSize(dim);
		label.setMinimumSize(dim);
		label.setMaximumSize(dim);
	}
	@Override public void setDescription(String desc) {
		this.desc = desc;
		update();
		label.setToolTipText(desc);
	}
	
	@Override public void update() {
		label.setFont(data.get() != null ? set_font : unset_font);
		label.setText(data.get() != null ? data.get().getName() : desc);
	}
}
