package satori.main;

import javax.swing.SwingUtilities;

public class SatoriTool {
	public static void main(String[] args) {
		SwingUtilities.invokeLater(new Runnable() {
			@Override public void run() { SFrame.get().start(); }
		});
	}
}
