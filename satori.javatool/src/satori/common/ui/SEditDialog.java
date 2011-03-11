package satori.common.ui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JFileChooser;
import javax.swing.JPanel;
import javax.swing.JScrollPane;

import satori.blob.SBlob;
import satori.common.SException;
import satori.main.SFrame;

public class SEditDialog {
	private SBlob blob;
	private JDialog dialog;
	private JEditorPane edit_pane;
	
	public SEditDialog() { initialize(); }
	
	private void initialize() {
		dialog = new JDialog(SFrame.get().getFrame(), true);
		dialog.getContentPane().setLayout(new BorderLayout());
		edit_pane = new JEditorPane();
		JScrollPane scroll_pane = new JScrollPane(edit_pane);
		dialog.getContentPane().add(scroll_pane, BorderLayout.CENTER);
		JPanel button_pane = new JPanel(new FlowLayout(FlowLayout.CENTER));
		JButton save = new JButton("Save");
		save.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				File file = blob.getFile();
				if (file == null) {
					JFileChooser file_chooser = new JFileChooser();
					String name = blob.getName();
					if (name != null && !name.isEmpty()) file_chooser.setSelectedFile(new File(file_chooser.getCurrentDirectory(), name));
					int ret = file_chooser.showDialog(SFrame.get().getFrame(), "Save");
					if (ret != JFileChooser.APPROVE_OPTION) return;
					file = file_chooser.getSelectedFile();
				}
				try { edit_pane.write(new OutputStreamWriter(new FileOutputStream(file))); }
				catch(IOException ex) { SFrame.showErrorDialog(new SException(ex)); }
				try { blob = SBlob.createLocal(file); }
				catch(SException ex) { SFrame.showErrorDialog(ex); }
			}
		});
		button_pane.add(save);
		JButton close = new JButton("Close");
		close.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				dialog.setVisible(false);
			}
		});
		button_pane.add(close);
		dialog.getContentPane().add(button_pane, BorderLayout.SOUTH);
		Dimension dim = SFrame.get().getFrame().getSize();
		dim.width -= 100; dim.height -= 100;
		dialog.setSize(dim);
		dialog.setLocationRelativeTo(SFrame.get().getFrame());
	}
	
	public SBlob process(SBlob blob) throws SException {
		this.blob = blob;
		String name = blob.getName();
		dialog.setTitle(name);
		if (name.endsWith(".java")) edit_pane.setContentType("text/java");
		else if (name.endsWith(".c")) edit_pane.setContentType("text/c");
		else if (name.endsWith(".cpp")) edit_pane.setContentType("text/cpp");
		else if (name.endsWith(".py")) edit_pane.setContentType("text/python");
		else edit_pane.setContentType("text/plain");
		File file = blob.getFile();
		boolean delete = false;
		if (file == null) {
			try { file = File.createTempFile("satori", null); }
			catch(IOException ex) { throw new SException(ex); }
			blob.saveLocal(file);
			delete = true;
		}
		try { edit_pane.read(new InputStreamReader(new FileInputStream(file)), null); }
		catch(IOException ex) { throw new SException(ex); }
		finally { if (delete) file.delete(); }
		dialog.setVisible(true);
		return this.blob;
	}
}
