package satori.main;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.Toolkit;
import java.awt.datatransfer.Clipboard;
import java.awt.datatransfer.StringSelection;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.io.Writer;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;

public class SUncaughtExceptionHandler implements Thread.UncaughtExceptionHandler {
	private JDialog dialog = null;
	private JTextArea log_area = null;
	
	private void showException(Thread thread, Throwable ex) {
		if (dialog != null) return;
		dialog = new JDialog(null, "Unexpected exception", JDialog.ModalityType.APPLICATION_MODAL);
		dialog.getContentPane().setLayout(new BorderLayout());
		JLabel label = new JLabel(
				"<html><p>An unexcpected exception occurred. Please send a bug report to " +
				"<tt>walczak@tcs.uj.edu.pl</tt> providing the information below. Note that " +
				"the application's internal state may have been corrupted and thus its " +
				"further use may lead to unpredictable results.</p></html>");
		label.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));
		dialog.getContentPane().add(label, BorderLayout.NORTH);
		log_area = new JTextArea();
		log_area.setEditable(false);
		log_area.setLineWrap(true);
		Writer stack_trace = new StringWriter();
		ex.printStackTrace(new PrintWriter(stack_trace));
		log_area.setText(stack_trace.toString());
		dialog.getContentPane().add(new JScrollPane(log_area), BorderLayout.CENTER);
		JButton clipboard_button = new JButton("Copy to clipboard");
		clipboard_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { copyToClipboard(); }
		});
		JButton close_button = new JButton("Close");
		close_button.addActionListener(new ActionListener() {
			@Override public void actionPerformed(ActionEvent e) { closeDialog(); }
		});
		JPanel button_pane = new JPanel(new FlowLayout(FlowLayout.CENTER, 5, 5));
		button_pane.add(clipboard_button);
		button_pane.add(close_button);
		dialog.getContentPane().add(button_pane, BorderLayout.SOUTH);
		dialog.setSize(740, 400);
		dialog.setLocationRelativeTo(null);
		dialog.setDefaultCloseOperation(JDialog.DO_NOTHING_ON_CLOSE);
		dialog.setVisible(true);
	}
	private void copyToClipboard() {
		Clipboard clipboard = Toolkit.getDefaultToolkit().getSystemClipboard();
		clipboard.setContents(new StringSelection(log_area.getText()), null);
	}
	private void closeDialog() {
		dialog.setVisible(false);
		dialog.dispose();
		log_area = null;
		dialog = null;
	}
	
    @Override public void uncaughtException(final Thread thread, final Throwable ex) {
        if (SwingUtilities.isEventDispatchThread()) showException(thread, ex);
        else SwingUtilities.invokeLater(new Runnable() {
            @Override public void run() { showException(thread, ex); }
        });
    }
}
