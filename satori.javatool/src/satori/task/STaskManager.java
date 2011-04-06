package satori.task;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.SwingUtilities;

import satori.main.SFrame;

public class STaskManager {
	private static class Monitor implements STaskLogger {
		private final STask task;
		private final JDialog dialog;
		private final JTextArea log_area;
		private final JButton abort_button, close_button;
		private final StringBuilder log = new StringBuilder();
		
		private Thread thread;
		private boolean success;
		
		public Monitor(STask task, JFrame frame) {
			this.task = task;
			dialog = new JDialog(frame, "Progress", true);
			dialog.getContentPane().setLayout(new BorderLayout());
			log_area = new JTextArea();
			log_area.setEditable(false);
			log_area.setLineWrap(true);
			dialog.getContentPane().add(new JScrollPane(log_area), BorderLayout.CENTER);
			abort_button = new JButton("Abort");
			abort_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { abortTask(); }
			});
			close_button = new JButton("Close");
			close_button.setEnabled(false);
			close_button.addActionListener(new ActionListener() {
				@Override public void actionPerformed(ActionEvent e) { closeDialog(); }
			});
			JPanel button_pane = new JPanel(new FlowLayout(FlowLayout.CENTER, 5, 5));
			button_pane.add(abort_button);
			button_pane.add(close_button);
			dialog.getContentPane().add(button_pane, BorderLayout.SOUTH);
			dialog.setSize(400, 300);
			dialog.setLocationRelativeTo(frame);
			dialog.setDefaultCloseOperation(JDialog.DO_NOTHING_ON_CLOSE);
		}
		
		private synchronized void abortTask() {
			if (thread != null) thread.interrupt();
		}
		private synchronized void updateLog() {
			log_area.setText(log.toString());
		}
		private synchronized void updateAfterFailure() {
			log_area.setText(log.toString());
			abort_button.setEnabled(false);
			close_button.setEnabled(true);
		}
		private synchronized void closeDialog() {
			dialog.setVisible(false);
			dialog.dispose();
		}
		
		@Override public synchronized void log(String message) {
			log.append(message + "\n");
			SwingUtilities.invokeLater(new Runnable() {
				@Override public void run() { updateLog(); }
			});
		}
		
		private synchronized void finishSuccess() {
			thread = null;
			success = true;
			SwingUtilities.invokeLater(new Runnable() {
				@Override public void run() { closeDialog(); }
			});
		}
		private synchronized void finishFailure(String message) {
			log.append(message + "\n");
			thread = null;
			success = false;
			SwingUtilities.invokeLater(new Runnable() {
				@Override public void run() { updateAfterFailure(); }
			});
		}
		private synchronized void runTask() {
			thread = new Thread(new Runnable() {
				@Override public void run() {
					try { task.run(Monitor.this); }
					catch(Throwable t) { finishFailure(t.getMessage()); return; }
					finishSuccess();
				}
			});
			thread.start();
		}
		private synchronized void checkSuccess() throws STaskException {
			if (!success) throw new STaskException();
		}
		
		public void execute() throws STaskException {
			runTask();
			dialog.setVisible(true);
			checkSuccess();
		}
	}
	
	public static void execute(STask task) throws STaskException {
		new Monitor(task, SFrame.get().getFrame()).execute();
	}
}
