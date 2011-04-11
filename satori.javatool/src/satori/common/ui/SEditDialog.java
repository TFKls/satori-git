package satori.common.ui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.FileWriter;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.Writer;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JFileChooser;
import javax.swing.JPanel;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;

import org.apache.commons.io.IOUtils;
import org.fife.ui.rsyntaxtextarea.RSyntaxTextArea;
import org.fife.ui.rsyntaxtextarea.SyntaxConstants;
import org.fife.ui.rtextarea.RTextScrollPane;

import satori.data.SBlob;
import satori.main.SFrame;
import satori.task.SResultTask;
import satori.task.STask;
import satori.task.STaskException;
import satori.task.STaskManager;

public class SEditDialog {
	private SBlob blob;
	private JDialog dialog;
	private RSyntaxTextArea edit_pane;
	private boolean modified = true;
	
	public SEditDialog() { initialize(); }
	
	private void initialize() {
		dialog = new JDialog(SFrame.get().getFrame(), true);
		dialog.getContentPane().setLayout(new BorderLayout());
		edit_pane = new RSyntaxTextArea();
		edit_pane.setClearWhitespaceLinesEnabled(false);
		edit_pane.setHighlightCurrentLine(false);
		edit_pane.setTabSize(4);
		edit_pane.getDocument().addDocumentListener(new DocumentListener() {
			@Override public void changedUpdate(DocumentEvent e) { setModified(true); }
			@Override public void insertUpdate(DocumentEvent e) { setModified(true); }
			@Override public void removeUpdate(DocumentEvent e) { setModified(true); }
		});
		RTextScrollPane scroll_pane = new RTextScrollPane(edit_pane);
		dialog.getContentPane().add(scroll_pane, BorderLayout.CENTER);
		JPanel button_pane = new JPanel(new FlowLayout(FlowLayout.CENTER));
		JButton save = new JButton("Save");
		save.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				File file = blob != null ? blob.getFile() : null;
				if (file == null) file = saveAs();
				if (file == null) return;
				try { blob = createPane(file); }
				catch(STaskException ex) { return; }
				setModified(false);
			}
		});
		button_pane.add(save);
		JButton close = new JButton("Close");
		close.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) {
				if (modified && !SFrame.showWarningDialog("Unsaved changes will be lost.")) return;
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
	
	private void setModified(boolean modified) {
		if (modified == this.modified) return;
		this.modified = modified;
		String title = blob != null ? blob.getName() : "No name";
		if (modified) title += "*";
		dialog.setTitle(title);
	}
	private File saveAs() {
		JFileChooser file_chooser = new JFileChooser();
		String name = blob != null ? blob.getName() : null;
		if (name != null && !name.isEmpty()) file_chooser.setSelectedFile(new File(file_chooser.getCurrentDirectory(), name));
		int ret = file_chooser.showDialog(SFrame.get().getFrame(), "Save");
		if (ret != JFileChooser.APPROVE_OPTION) return null;
		return file_chooser.getSelectedFile();
	}
	private SBlob createPane(final File file) throws STaskException {
		return STaskManager.execute(new SResultTask<SBlob>() {
			@Override public SBlob run() throws Exception {
				STaskManager.log("Saving blob...");
				Writer writer = new FileWriter(file);
				try { edit_pane.write(writer); }
				finally { IOUtils.closeQuietly(writer); }
				return SBlob.createLocalTask(file);
			}
		});
	}
	private void loadPane() throws STaskException {
		STaskManager.execute(new STask() {
			@Override public void run() throws Exception {
				STaskManager.log(blob.getFile() != null ? "Loading local file..." : "Loading blob...");
				Reader reader = new InputStreamReader(blob.getStreamTask());
				try { edit_pane.read(reader, null); }
				finally { IOUtils.closeQuietly(reader); }
			}
		});
	}
	
	public SBlob process(SBlob blob) throws STaskException {
		this.blob = blob;
		String name = blob != null ? blob.getName() : "";
		if (name.endsWith(".java")) edit_pane.setSyntaxEditingStyle(SyntaxConstants.SYNTAX_STYLE_JAVA);
		else if (name.endsWith(".c")) edit_pane.setSyntaxEditingStyle(SyntaxConstants.SYNTAX_STYLE_C);
		else if (name.endsWith(".cpp")) edit_pane.setSyntaxEditingStyle(SyntaxConstants.SYNTAX_STYLE_CPLUSPLUS);
		else if (name.endsWith(".py")) edit_pane.setSyntaxEditingStyle(SyntaxConstants.SYNTAX_STYLE_PYTHON);
		else edit_pane.setSyntaxEditingStyle(SyntaxConstants.SYNTAX_STYLE_NONE);
		if (blob != null) loadPane();
		edit_pane.setCaretPosition(0);
		edit_pane.discardAllEdits();
		setModified(false);
		dialog.setVisible(true);
		return this.blob;
	}
}
